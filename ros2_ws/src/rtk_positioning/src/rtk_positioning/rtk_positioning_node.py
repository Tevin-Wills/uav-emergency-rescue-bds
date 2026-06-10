"""
RTK positioning node — supports Level 1, Level 2, and Level 3 modes.

This is the main simulation node. It:
  - Subscribes to the simulated UAV ground-truth position (/uav/ground_truth)
  - Subscribes to the base station coordinate (/rtk/base_station)
  - Publishes raw GNSS position with larger noise (/uav/raw_gps)
  - Publishes RTK-corrected position with smaller noise (/uav/rtk_position)
  - Publishes RTK status (/uav/rtk_status)
  - Publishes model-based accuracy metrics (/rtk/accuracy)
  - Publishes actual measured position errors (/rtk/error_metrics)
  - [Level 3] Publishes mission viability signal (/rtk/mission_viability)

IMPORTANT — simulation disclaimer:
  This node does not process real RTCM correction data.
  It does not decode carrier-phase measurements.
  It does not simulate real BeiDou/GPS satellite signals.
  RTK correction is modelled as noise reduction based on simulated fix state.

/uav/rtk_status format (std_msgs/String):
  "<status_code>|<status_name>|<accuracy_m>"
  Example: "3|RTK_FIXED|0.0300"

/rtk/accuracy format (Float32MultiArray):
  [raw_gnss_std_m, rtk_std_m, improvement_percent]
  Level 3: values are computed dynamically from correction quality and age.

/rtk/error_metrics format (Float32MultiArray):
  [raw_gnss_error_m, rtk_error_m]
  Actual 3D Euclidean errors measured against ground truth.

/rtk/mission_viability format (std_msgs/String) — Level 3 only:
  APPROACH_VIABLE   accuracy <= viability_approach_threshold_m (default 2.0 m)
  LANDING_VIABLE    accuracy <= viability_landing_threshold_m  (default 0.3 m)
  DEGRADED          accuracy between landing and approach thresholds
  INSUFFICIENT      accuracy > approach threshold

Dynamic uncertainty (Level 3, use_dynamic_uncertainty: true):
  RTK_FIXED:       base_std * (1 + (1 - quality) * 2.0)
  RTK_FLOAT:       base_std * (1 + (1 - quality) * 1.5)
  GNSS_ONLY:       gnss_noise_std_m from RTCM message
  CORRECTION_LOST: gnss_noise_std_m + age_sec * 0.05, capped at gnss_noise * 2.0
"""

import numpy as np
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import String, Float32, Float32MultiArray

from rtk_positioning.gnss_noise_model import GnssNoiseModel
from rtk_positioning.rtk_correction_model import RtkCorrectionModel
from rtk_positioning.coordinate_transform import enu_to_wgs84, wgs84_to_enu
from rtk_positioning.rtk_status_manager import RtkStatusManager
from rtk_positioning import rtk_error_model
from interfaces.msg import SimulatedRtcm

# Drift rate applied to CORRECTION_LOST uncertainty (metres per second without corrections).
_CORRECTION_LOST_DRIFT_RATE_M_S = 0.05


class RtkPositioningNode(Node):

    def __init__(self):
        super().__init__('rtk_positioning_node')

        # ── Base station defaults ─────────────────────────────────────────────
        self.declare_parameter('base_station.latitude',  39.981000)
        self.declare_parameter('base_station.longitude', 116.344000)
        self.declare_parameter('base_station.altitude',  50.0)

        # ── Noise parameters (loaded from config/noise_profiles.yaml) ─────────
        self.declare_parameter('noise.normal_gnss_std_m',    1.5)
        self.declare_parameter('noise.rtk_float_std_m',      0.25)
        self.declare_parameter('noise.rtk_fixed_std_m',      0.03)
        self.declare_parameter('noise.correction_lost_std_m', 2.5)

        # ── Level 2: correction-message-based status control ──────────────────
        self.declare_parameter('use_simulated_rtcm',      False)
        self.declare_parameter('simulated_rtcm_topic',    '/rtk/simulated_rtcm')
        self.declare_parameter('correction_timeout_sec',  2.0)
        self.declare_parameter('float_quality_threshold', 0.4)
        self.declare_parameter('fixed_quality_threshold', 0.8)

        # ── Level 3: dynamic uncertainty and mission viability ────────────────
        self.declare_parameter('use_dynamic_uncertainty',         False)
        self.declare_parameter('viability_approach_threshold_m',  2.0)
        self.declare_parameter('viability_landing_threshold_m',   0.3)

        # ── Realistic offset base station + RTK error budget (opt-in) ─────────
        # world_origin is the ENU/output anchor (where the drone's metres are
        # measured from) — MUST match px4_pose_adapter's world_origin. The base
        # station is then a SEPARATE coordinate, free to be offset from the drone.
        self.declare_parameter('world_origin.latitude',  47.397971057728981)
        self.declare_parameter('world_origin.longitude', 8.5461637398001447)
        self.declare_parameter('world_origin.altitude',  0.0)
        # When False (default), behaviour is identical to before (L3 reproducible):
        # output is anchored on world_origin (== base when co-located) and no
        # baseline error/state degradation is applied.
        self.declare_parameter('enable_baseline_error_model', False)
        self.declare_parameter('rtk_baseline_ppm',        1.0)    # mm per km (1 ppm)
        self.declare_parameter('baseline_fixed_limit_km', 20.0)   # > this: cannot hold FIXED
        self.declare_parameter('baseline_max_km',         50.0)   # > this: GNSS only

        self._base_lat = self.get_parameter('base_station.latitude').value
        self._base_lon = self.get_parameter('base_station.longitude').value
        self._base_alt = self.get_parameter('base_station.altitude').value

        self._origin_lat = self.get_parameter('world_origin.latitude').value
        self._origin_lon = self.get_parameter('world_origin.longitude').value
        self._origin_alt = self.get_parameter('world_origin.altitude').value
        self._enable_baseline_model   = self.get_parameter('enable_baseline_error_model').value
        self._baseline_ppm            = self.get_parameter('rtk_baseline_ppm').value
        self._baseline_fixed_limit_km = self.get_parameter('baseline_fixed_limit_km').value
        self._baseline_max_km         = self.get_parameter('baseline_max_km').value

        self._noise_model = GnssNoiseModel(seed=42)
        self._noise_model.update_from_config({
            'normal_gnss_std_m':     self.get_parameter('noise.normal_gnss_std_m').value,
            'rtk_float_std_m':       self.get_parameter('noise.rtk_float_std_m').value,
            'rtk_fixed_std_m':       self.get_parameter('noise.rtk_fixed_std_m').value,
            'correction_lost_std_m': self.get_parameter('noise.correction_lost_std_m').value,
        })

        self._correction_model = RtkCorrectionModel(self._noise_model)
        self._status_manager   = RtkStatusManager()
        self._start_time       = None

        self._use_l2                  = self.get_parameter('use_simulated_rtcm').value
        self._correction_timeout_sec  = self.get_parameter('correction_timeout_sec').value
        self._float_quality_threshold = self.get_parameter('float_quality_threshold').value
        self._fixed_quality_threshold = self.get_parameter('fixed_quality_threshold').value
        self._latest_rtcm             = None
        self._last_rtcm_time          = None
        self._had_corrections         = False

        self._use_dynamic_uncertainty      = self.get_parameter('use_dynamic_uncertainty').value
        self._viability_approach_threshold = self.get_parameter('viability_approach_threshold_m').value
        self._viability_landing_threshold  = self.get_parameter('viability_landing_threshold_m').value

        # Dynamic uncertainty state — updated from each incoming RTCM message.
        self._current_gnss_noise_std   = self._noise_model.get_std('GNSS_ONLY')
        self._current_correction_quality = 0.0
        self._current_correction_age     = 0.0

        # ── Subscriptions ─────────────────────────────────────────────────────
        self.create_subscription(
            Odometry, '/uav/ground_truth', self._ground_truth_cb, 10)
        self.create_subscription(
            NavSatFix, '/rtk/base_station', self._base_station_cb, 10)
        if self._use_l2:
            rtcm_topic = self.get_parameter('simulated_rtcm_topic').value
            self.create_subscription(SimulatedRtcm, rtcm_topic, self._rtcm_cb, 10)

        # ── Publishers ────────────────────────────────────────────────────────
        self._pub_raw_gps       = self.create_publisher(NavSatFix,         '/uav/raw_gps',             10)
        self._pub_rtk_pos       = self.create_publisher(NavSatFix,         '/uav/rtk_position',        10)
        self._pub_rtk_status    = self.create_publisher(String,            '/uav/rtk_status',          10)
        self._pub_accuracy      = self.create_publisher(Float32MultiArray, '/rtk/accuracy',             10)
        self._pub_error_metrics = self.create_publisher(Float32MultiArray, '/rtk/error_metrics',       10)
        self._pub_viability     = self.create_publisher(String,            '/rtk/mission_viability',   10)
        self._pub_baseline      = self.create_publisher(Float32,           '/rtk/baseline_km',         10)

        mode = (
            'Level 3 — resilient RTK / disaster scenario'
            if self._use_dynamic_uncertainty else
            'Level 2 — PX4/Gazebo integration'
            if self._use_l2 else
            'Level 1 — standalone simulation'
        )
        self.get_logger().info(
            f'RTK positioning node started — {mode}\n'
            f'  noise GNSS_ONLY={self._noise_model.get_std("GNSS_ONLY")} m  '
            f'RTK_FLOAT={self._noise_model.get_std("RTK_FLOAT")} m  '
            f'RTK_FIXED={self._noise_model.get_std("RTK_FIXED")} m\n'
            f'  dynamic_uncertainty={self._use_dynamic_uncertainty}'
        )

    # ── Subscription callbacks ────────────────────────────────────────────────

    def _base_station_cb(self, msg: NavSatFix):
        self._base_lat = msg.latitude
        self._base_lon = msg.longitude
        self._base_alt = msg.altitude

    def _rtcm_cb(self, msg: SimulatedRtcm):
        self._latest_rtcm    = msg
        self._last_rtcm_time = self.get_clock().now()

        if self._use_dynamic_uncertainty:
            # Update the noise model so apply_raw_gnss reflects the current phase noise.
            gnss_std = float(msg.gnss_noise_std_m) if msg.gnss_noise_std_m > 0.0 else self._current_gnss_noise_std
            self._current_gnss_noise_std = gnss_std
            self._noise_model.update_from_config({'normal_gnss_std_m': gnss_std})

        self._current_correction_quality = float(msg.correction_quality)
        self._current_correction_age     = float(msg.correction_age_sec)

    # ── Main processing callback ──────────────────────────────────────────────

    def _ground_truth_cb(self, msg: Odometry):
        now = self.get_clock().now()
        if self._start_time is None:
            self._start_time = now

        elapsed_sec = (now - self._start_time).nanoseconds * 1e-9

        if self._use_l2:
            rtk_status = self._get_l2_status()
            self._status_manager.force_status(rtk_status)
        else:
            rtk_status = self._status_manager.update(elapsed_sec)

        true_pos = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z,
        ])

        # Baseline = horizontal distance from the base station to the drone,
        # both in ENU about the world origin (informational when the model is off).
        baseline_km = self._compute_baseline_km(true_pos)

        # Raw GNSS (standalone, baseline-independent) — drawn first so the noise
        # sequence is unchanged vs. the previous implementation.
        raw_pos = self._correction_model.apply_raw_gnss(true_pos)

        baseline_term_m = 0.0
        if self._enable_baseline_model:
            # Fix state degrades realistically with baseline (recoverable).
            rtk_status = rtk_error_model.degrade_status_for_baseline(
                rtk_status, baseline_km,
                self._baseline_fixed_limit_km, self._baseline_max_km)
            self._status_manager.force_status(rtk_status)
            baseline_term_m = rtk_error_model.baseline_term_m(baseline_km, self._baseline_ppm)
            # Inject error consistent with the budget (status floor + baseline term).
            floor_std = self._noise_model.get_std(rtk_status)
            sigma_inj = rtk_error_model.rtk_sigma_m(floor_std, baseline_km, self._baseline_ppm)
            rtk_pos = self._noise_model.apply_noise_value(true_pos, sigma_inj)
        else:
            rtk_pos = self._correction_model.apply_correction(true_pos, rtk_status)

        raw_error_m = float(np.linalg.norm(raw_pos - true_pos))
        rtk_error_m = float(np.linalg.norm(rtk_pos - true_pos))

        # Output anchored on the WORLD ORIGIN (not the base) so the reported
        # position is correct regardless of where the base station sits.
        raw_lat, raw_lon, raw_alt = enu_to_wgs84(
            self._origin_lat, self._origin_lon, self._origin_alt,
            raw_pos[0], raw_pos[1], raw_pos[2])

        rtk_lat, rtk_lon, rtk_alt = enu_to_wgs84(
            self._origin_lat, self._origin_lon, self._origin_alt,
            rtk_pos[0], rtk_pos[1], rtk_pos[2])

        stamp = now.to_msg()
        raw_std, rtk_std = self._get_uncertainty(rtk_status)
        if self._enable_baseline_model:
            rtk_std = float(np.hypot(rtk_std, baseline_term_m))

        self._publish_raw_gps(stamp, raw_lat, raw_lon, raw_alt, raw_std)
        self._publish_rtk_position(stamp, rtk_lat, rtk_lon, rtk_alt, rtk_std)
        self._publish_rtk_status(rtk_status, rtk_std)
        self._publish_accuracy(raw_std, rtk_std)
        self._publish_error_metrics(raw_error_m, rtk_error_m)
        self._pub_baseline.publish(Float32(data=float(baseline_km)))

        if self._use_dynamic_uncertainty:
            self._publish_mission_viability(rtk_std)

    def _compute_baseline_km(self, true_pos):
        """Horizontal base->drone distance (km), both in ENU about the world origin."""
        base_e, base_n, _ = wgs84_to_enu(
            self._origin_lat, self._origin_lon, self._origin_alt,
            self._base_lat, self._base_lon, self._base_alt)
        return float(np.hypot(true_pos[0] - base_e, true_pos[1] - base_n)) / 1000.0

    # ── Level 2 status derivation ─────────────────────────────────────────────

    def _get_l2_status(self):
        """Derive RTK status from the latest simulated correction message."""
        if self._latest_rtcm is None:
            return 'GNSS_ONLY'

        msg_age = (self.get_clock().now() - self._last_rtcm_time).nanoseconds * 1e-9
        if msg_age > self._correction_timeout_sec:
            return 'CORRECTION_LOST'

        rtcm = self._latest_rtcm
        if not rtcm.correction_available:
            return 'CORRECTION_LOST' if self._had_corrections else 'GNSS_ONLY'

        self._had_corrections = True
        if rtcm.correction_quality >= self._fixed_quality_threshold:
            return 'RTK_FIXED'
        elif rtcm.correction_quality >= self._float_quality_threshold:
            return 'RTK_FLOAT'
        return 'GNSS_ONLY'

    # ── Uncertainty calculation ───────────────────────────────────────────────

    def _get_uncertainty(self, rtk_status):
        """
        Return (raw_gnss_std_m, rtk_std_m).

        Level 3 dynamic mode: uncertainty is computed from correction quality,
        correction age, and phase GNSS noise. Level 1/2 mode: fixed noise model values.
        """
        raw_std = self._noise_model.get_std('GNSS_ONLY')

        if not self._use_dynamic_uncertainty:
            return raw_std, self._noise_model.get_std(rtk_status)

        gnss_noise = self._current_gnss_noise_std
        quality    = self._current_correction_quality
        age        = self._current_correction_age

        if rtk_status == 'RTK_FIXED':
            base = self._noise_model.get_std('RTK_FIXED')
            rtk_std = base * (1.0 + (1.0 - quality) * 2.0)
        elif rtk_status == 'RTK_FLOAT':
            base = self._noise_model.get_std('RTK_FLOAT')
            rtk_std = base * (1.0 + (1.0 - quality) * 1.5)
        elif rtk_status == 'CORRECTION_LOST':
            drift = age * _CORRECTION_LOST_DRIFT_RATE_M_S
            rtk_std = min(gnss_noise + drift, gnss_noise * 2.0)
        else:  # GNSS_ONLY
            rtk_std = gnss_noise

        return gnss_noise, rtk_std

    # ── Publishers ────────────────────────────────────────────────────────────

    def _publish_raw_gps(self, stamp, lat, lon, alt, std):
        msg = NavSatFix()
        msg.header.stamp      = stamp
        msg.header.frame_id   = 'gps'
        msg.status.status     = NavSatStatus.STATUS_FIX
        msg.status.service    = NavSatStatus.SERVICE_GPS
        msg.latitude          = lat
        msg.longitude         = lon
        msg.altitude          = alt
        cov = std ** 2
        msg.position_covariance = [cov, 0.0, 0.0,
                                   0.0, cov, 0.0,
                                   0.0, 0.0, cov]
        msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
        self._pub_raw_gps.publish(msg)

    def _publish_rtk_position(self, stamp, lat, lon, alt, std):
        msg = NavSatFix()
        msg.header.stamp    = stamp
        msg.header.frame_id = 'gps'
        code = self._status_manager.status_code
        if code >= 3:
            msg.status.status = NavSatStatus.STATUS_GBAS_FIX
        elif code >= 2:
            msg.status.status = NavSatStatus.STATUS_SBAS_FIX
        else:
            msg.status.status = NavSatStatus.STATUS_FIX
        msg.status.service = NavSatStatus.SERVICE_GPS
        msg.latitude       = lat
        msg.longitude      = lon
        msg.altitude       = alt
        cov = std ** 2
        msg.position_covariance = [cov, 0.0, 0.0,
                                   0.0, cov, 0.0,
                                   0.0, 0.0, cov]
        msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
        self._pub_rtk_pos.publish(msg)

    def _publish_rtk_status(self, status_name, rtk_std):
        msg = String()
        msg.data = (
            f'{self._status_manager.status_code}|'
            f'{status_name}|'
            f'{rtk_std:.4f}'
        )
        self._pub_rtk_status.publish(msg)

    def _publish_accuracy(self, raw_std, rtk_std):
        improvement = (1.0 - rtk_std / raw_std) * 100.0 if raw_std > 0 else 0.0
        msg = Float32MultiArray()
        msg.data = [float(raw_std), float(rtk_std), float(improvement)]
        self._pub_accuracy.publish(msg)

    def _publish_error_metrics(self, raw_error_m, rtk_error_m):
        msg = Float32MultiArray()
        msg.data = [raw_error_m, rtk_error_m]
        self._pub_error_metrics.publish(msg)

    def _publish_mission_viability(self, rtk_std):
        if rtk_std <= self._viability_landing_threshold:
            viability = 'LANDING_VIABLE'
        elif rtk_std <= self._viability_approach_threshold:
            viability = 'APPROACH_VIABLE'
        elif rtk_std <= self._viability_approach_threshold * 2.0:
            viability = 'DEGRADED'
        else:
            viability = 'INSUFFICIENT'
        msg = String()
        msg.data = viability
        self._pub_viability.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = RtkPositioningNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
