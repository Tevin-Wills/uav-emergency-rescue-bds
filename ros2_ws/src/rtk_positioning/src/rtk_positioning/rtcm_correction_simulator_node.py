"""
Simulated GPS_RTCM_DATA-style correction simulator for Level 2.

Publishes correction condition information on /rtk/simulated_rtcm.

IMPORTANT — simulation disclaimer:
  This node does NOT publish real RTCM binary data.
  This node does NOT inject real MAVLink GPS_RTCM_DATA into PX4.
  This node does NOT decode or process real correction streams.
  It models correction availability, quality, age, and loss events
  so the RTK positioning node can react with realistic status transitions.

Simulated correction profile (time from node start):
  0–5 s   : correction_available=False  quality=0.0  → drives GNSS_ONLY
  5–15 s  : correction_available=True   quality=0.5  → drives RTK_FLOAT
  15–45 s : correction_available=True   quality=0.95 → drives RTK_FIXED
  45–50 s : correction_available=False  quality=0.0  → drives CORRECTION_LOST
  50+ s   : correction_available=True   quality=0.95 → drives RTK_FIXED (recovery)
"""

import rclpy
from rclpy.node import Node
from interfaces.msg import SimulatedRtcm


class RtcmCorrectionSimulatorNode(Node):

    def __init__(self):
        super().__init__('rtcm_correction_simulator_node')

        self.declare_parameter('publish_rate_hz',       5.0)
        self.declare_parameter('correction_source',     'simulated_base_station')
        self.declare_parameter('stable_quality',        0.95)
        self.declare_parameter('float_quality',         0.5)
        self.declare_parameter('lost_quality',          0.0)
        self.declare_parameter('simulated_length_bytes', 120)

        rate_hz                  = self.get_parameter('publish_rate_hz').value
        self._correction_source  = self.get_parameter('correction_source').value
        self._stable_quality     = float(self.get_parameter('stable_quality').value)
        self._float_quality      = float(self.get_parameter('float_quality').value)
        self._lost_quality       = float(self.get_parameter('lost_quality').value)
        self._sim_length         = int(self.get_parameter('simulated_length_bytes').value)

        self._pub = self.create_publisher(SimulatedRtcm, '/rtk/simulated_rtcm', 10)

        self._start_time        = None
        self._last_avail_time   = None
        self._seq_id            = 0

        self.create_timer(1.0 / rate_hz, self._publish_cb)

        self.get_logger().info(
            'RTCM correction simulator started '
            '(simulated behavior only — not real RTCM data)\n'
            f'  rate={rate_hz} Hz  source={self._correction_source}'
        )

    # ------------------------------------------------------------------
    def _correction_state(self, elapsed_sec):
        """Return (correction_available, correction_quality) for elapsed time."""
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

    # ------------------------------------------------------------------
    def _publish_cb(self):
        now = self.get_clock().now()
        if self._start_time is None:
            self._start_time      = now
            self._last_avail_time = now

        elapsed_sec = (now - self._start_time).nanoseconds * 1e-9
        available, quality = self._correction_state(elapsed_sec)

        if available:
            self._last_avail_time = now
            age_sec = 0.0
        else:
            age_sec = (now - self._last_avail_time).nanoseconds * 1e-9

        msg = SimulatedRtcm()
        msg.header.stamp       = now.to_msg()
        msg.header.frame_id    = 'base_station'
        msg.sequence_id        = self._seq_id % 256
        msg.fragment_id        = 0
        msg.fragmented         = False
        msg.length             = self._sim_length if available else 0
        msg.correction_available = available
        msg.correction_age_sec   = float(age_sec)
        msg.correction_quality   = float(quality)
        msg.correction_source    = self._correction_source

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
