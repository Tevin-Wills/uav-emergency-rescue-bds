"""
Simulated GPS_RTCM_DATA-style correction simulator.

Supports two operating modes selected by the `use_phase_profile` parameter:

Level 2 mode (use_phase_profile: false — default):
  Fixed correction profile matching the original Level 2 schedule:
    0–5 s   : correction_available=False  quality=0.0  → drives GNSS_ONLY
    5–15 s  : correction_available=True   quality=0.5  → drives RTK_FLOAT
    15–45 s : correction_available=True   quality=0.95 → drives RTK_FIXED
    45–50 s : correction_available=False  quality=0.0  → drives CORRECTION_LOST
    50+ s   : correction_available=True   quality=0.95 → drives RTK_FIXED (recovery)

Level 3 mode (use_phase_profile: true):
  Time-varying compound disaster scenario driven by a phase profile loaded from
  the config YAML (passed via the `config_file` parameter). Each phase defines
  GNSS noise, correction quality, and a periodic correction gap schedule. Noise
  and quality ramp linearly across phases that specify _start/_end values.

IMPORTANT — simulation disclaimer:
  This node does NOT publish real RTCM binary data.
  This node does NOT inject real MAVLink GPS_RTCM_DATA into PX4.
  It models correction availability, quality, age, and GNSS noise level so the
  RTK positioning node can react with realistic status transitions and noise.
"""

import yaml
import rclpy
from rclpy.node import Node
from interfaces.msg import SimulatedRtcm

# Baseline GNSS noise std in metres — used in Level 2 mode and as fallback.
_BASELINE_GNSS_NOISE_STD_M = 1.5


class RtcmCorrectionSimulatorNode(Node):

    def __init__(self):
        super().__init__('rtcm_correction_simulator_node')

        # ── Parameters shared by both modes ───────────────────────────────────
        self.declare_parameter('publish_rate_hz',         5.0)
        self.declare_parameter('correction_source',       'simulated_base_station')
        self.declare_parameter('simulated_length_bytes',  120)
        self.declare_parameter('use_phase_profile',       False)

        # ── Level 2 fixed-schedule parameters ────────────────────────────────
        self.declare_parameter('stable_quality',  0.95)
        self.declare_parameter('float_quality',   0.5)
        self.declare_parameter('lost_quality',    0.0)

        # ── Level 3 parameters ────────────────────────────────────────────────
        # config_file: absolute path to the scenario YAML, set by the launch file.
        # gnss_noise_override_std_m: fixed noise for total-failure mode (no profile).
        self.declare_parameter('config_file',               '')
        self.declare_parameter('gnss_noise_override_std_m', _BASELINE_GNSS_NOISE_STD_M)

        rate_hz                   = self.get_parameter('publish_rate_hz').value
        self._correction_source   = self.get_parameter('correction_source').value
        self._sim_length          = int(self.get_parameter('simulated_length_bytes').value)
        self._use_phase_profile   = self.get_parameter('use_phase_profile').value

        self._stable_quality      = float(self.get_parameter('stable_quality').value)
        self._float_quality       = float(self.get_parameter('float_quality').value)
        self._lost_quality        = float(self.get_parameter('lost_quality').value)
        self._gnss_noise_override = float(self.get_parameter('gnss_noise_override_std_m').value)

        self._phases = []
        if self._use_phase_profile:
            config_file = self.get_parameter('config_file').value
            if config_file:
                self._phases = self._load_phases(config_file)
            else:
                self.get_logger().error(
                    'use_phase_profile=true but config_file is empty — '
                    'falling back to Level 2 fixed schedule'
                )
                self._use_phase_profile = False

        self._pub = self.create_publisher(SimulatedRtcm, '/rtk/simulated_rtcm', 10)

        self._start_time      = None
        self._last_avail_time = None
        self._seq_id          = 0

        self.create_timer(1.0 / rate_hz, self._publish_cb)

        mode_str = 'phase profile (Level 3)' if self._use_phase_profile else 'fixed schedule (Level 2)'
        self.get_logger().info(
            f'RTCM correction simulator started — {mode_str}\n'
            f'  rate={rate_hz} Hz  source={self._correction_source}'
        )

    # ── Phase profile loading ─────────────────────────────────────────────────

    def _load_phases(self, config_file):
        """Read the phase_profile list from the scenario YAML."""
        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
            node_params = (
                config
                .get('rtcm_correction_simulator_node', {})
                .get('ros__parameters', {})
            )
            phases = node_params.get('phase_profile', [])
            if not phases:
                self.get_logger().warn(
                    f'No phase_profile entries found in {config_file}'
                )
            else:
                self.get_logger().info(
                    f'Loaded {len(phases)} mission phases from {config_file}'
                )
            return phases
        except Exception as exc:
            self.get_logger().error(
                f'Failed to load phase profile from {config_file}: {exc}\n'
                'Falling back to Level 2 fixed schedule.'
            )
            self._use_phase_profile = False
            return []

    # ── State computation — Level 2 fixed schedule ────────────────────────────

    def _correction_state_fixed(self, elapsed_sec):
        """Return (available, quality) for the original Level 2 fixed schedule."""
        if elapsed_sec < 5.0:
            return False, self._lost_quality
        elif elapsed_sec < 15.0:
            return True, self._float_quality
        elif elapsed_sec < 45.0:
            return True, self._stable_quality
        elif elapsed_sec < 50.0:
            return False, self._lost_quality
        else:
            return True, self._stable_quality

    # ── State computation — Level 3 phase profile ─────────────────────────────

    def _get_phase_state(self, elapsed_sec):
        """
        Return (available, quality, gnss_noise_std_m) for the current mission phase.

        Noise and quality ramp linearly across phases that define _start/_end values.
        Correction gaps are periodic within the phase: corrections are available for
        the first (interval - duration) seconds of each cycle, then lost for
        `duration` seconds.
        """
        current_phase = None
        for phase in self._phases:
            if phase['start_sec'] <= elapsed_sec < phase['end_sec']:
                current_phase = phase
                break

        if current_phase is None:
            # Beyond all defined phases — hold last phase values.
            current_phase = self._phases[-1] if self._phases else {}

        phase_start    = float(current_phase.get('start_sec', 0.0))
        phase_end      = float(current_phase.get('end_sec', phase_start))
        phase_duration = phase_end - phase_start
        phase_elapsed  = elapsed_sec - phase_start
        t = (phase_elapsed / phase_duration) if phase_duration > 0.0 else 0.0
        t = max(0.0, min(1.0, t))

        # GNSS noise — single value or linear ramp.
        if 'gnss_noise_std_m' in current_phase:
            gnss_noise = float(current_phase['gnss_noise_std_m'])
        else:
            n0 = float(current_phase.get('gnss_noise_std_m_start', _BASELINE_GNSS_NOISE_STD_M))
            n1 = float(current_phase.get('gnss_noise_std_m_end',   _BASELINE_GNSS_NOISE_STD_M))
            gnss_noise = n0 + t * (n1 - n0)

        # Correction quality — single value or linear ramp.
        if 'correction_quality' in current_phase:
            quality = float(current_phase['correction_quality'])
        else:
            q0 = float(current_phase.get('correction_quality_start', self._stable_quality))
            q1 = float(current_phase.get('correction_quality_end',   self._stable_quality))
            quality = q0 + t * (q1 - q0)

        # Correction gap schedule: gap occurs at the END of each cycle so the
        # UAV has corrections at phase entry before the first gap hits.
        gap_interval = float(current_phase.get('correction_gap_interval_sec', 0.0))
        gap_duration = float(current_phase.get('correction_gap_duration_sec', 0.0))

        available = True
        if gap_interval > 0.0 and gap_duration > 0.0:
            cycle_pos = phase_elapsed % gap_interval
            # Gap occupies the last `gap_duration` seconds of each cycle.
            available = cycle_pos < (gap_interval - gap_duration)

        return available, quality, gnss_noise

    # ── Publisher callback ────────────────────────────────────────────────────

    def _publish_cb(self):
        now = self.get_clock().now()
        if self._start_time is None:
            self._start_time      = now
            self._last_avail_time = now

        elapsed_sec = (now - self._start_time).nanoseconds * 1e-9

        if self._use_phase_profile:
            available, quality, gnss_noise_std = self._get_phase_state(elapsed_sec)
        else:
            available, quality = self._correction_state_fixed(elapsed_sec)
            gnss_noise_std = self._gnss_noise_override

        if available:
            self._last_avail_time = now
            age_sec = 0.0
        else:
            age_sec = (now - self._last_avail_time).nanoseconds * 1e-9

        msg = SimulatedRtcm()
        msg.header.stamp         = now.to_msg()
        msg.header.frame_id      = 'base_station'
        msg.sequence_id          = self._seq_id % 256
        msg.fragment_id          = 0
        msg.fragmented           = False
        msg.length               = self._sim_length if available else 0
        msg.correction_available = available
        msg.correction_age_sec   = float(age_sec)
        msg.correction_quality   = float(quality)
        msg.correction_source    = self._correction_source
        msg.gnss_noise_std_m     = float(gnss_noise_std)

        self._pub.publish(msg)
        self._seq_id += 1


def main(args=None):
    rclpy.init(args=args)
    node = RtcmCorrectionSimulatorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
