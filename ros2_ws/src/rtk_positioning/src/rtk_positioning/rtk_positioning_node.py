"""
RTK positioning node — supports Level 1 (standalone) and Level 2 (PX4/Gazebo) modes.

This is the main simulation node. It:
  - Subscribes to the simulated UAV ground-truth position (/uav/ground_truth)
  - Subscribes to the base station coordinate (/rtk/base_station)
  - Publishes raw GNSS position with larger noise (/uav/raw_gps)
  - Publishes RTK-corrected position with smaller noise (/uav/rtk_position)
  - Publishes RTK status (/uav/rtk_status)
  - Publishes model-based accuracy metrics (/rtk/accuracy)
  - Publishes actual measured position errors (/rtk/error_metrics)

IMPORTANT — Level 1 simulation disclaimer:
  This node does not process real RTCM correction data.
  It does not decode carrier-phase measurements.
  It does not simulate real BeiDou/GPS satellite signals.
  RTK correction is modelled as noise reduction based on simulated fix state.
  Status transitions are time-based (GNSS_ONLY → RTK_FLOAT → RTK_FIXED).

/uav/rtk_status format (Level 1 simplification — std_msgs/String):
  "<status_code>|<status_name>|<accuracy_m>"
  Example: "3|RTK_FIXED|0.0300"

/rtk/accuracy format (Level 1 simplification — Float32MultiArray):
  [raw_gnss_std_m, rtk_std_m, improvement_percent]

/rtk/error_metrics format (Float32MultiArray):
  [raw_gnss_error_m, rtk_error_m]
  These are actual 3D Euclidean errors measured against ground truth.
"""

import numpy as np
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import String, Float32MultiArray

from rtk_positioning.gnss_noise_model import GnssNoiseModel
from rtk_positioning.rtk_correction_model import RtkCorrectionModel
from rtk_positioning.coordinate_transform import enu_to_wgs84
from rtk_positioning.rtk_status_manager import RtkStatusManager
from interfaces.msg import SimulatedRtcm


class RtkPositioningNode(Node):

    def __init__(self):
        super().__init__('rtk_positioning_node')

        # Base station defaults — updated live from /rtk/base_station
        self.declare_parameter('base_station.latitude',  39.981000)
        self.declare_parameter('base_station.longitude', 116.344000)
        self.declare_parameter('base_station.altitude',  50.0)

        # Noise parameters — loaded from config/noise_profiles.yaml
        self.declare_parameter('noise.normal_gnss_std_m',    1.5)
        self.declare_parameter('noise.rtk_float_std_m',      0.25)
        self.declare_parameter('noise.rtk_fixed_std_m',      0.03)
        self.declare_parameter('noise.correction_lost_std_m', 2.5)

        # Level 2: correction-message-based status control
        self.declare_parameter('use_simulated_rtcm',      False)
        self.declare_parameter('simulated_rtcm_topic',    '/rtk/simulated_rtcm')
        self.declare_parameter('correction_timeout_sec',  2.0)
        self.declare_parameter('float_quality_threshold', 0.4)
        self.declare_parameter('fixed_quality_threshold', 0.8)

        self._base_lat = self.get_parameter('base_station.latitude').value
        self._base_lon = self.get_parameter('base_station.longitude').value
        self._base_alt = self.get_parameter('base_station.altitude').value

        self._noise_model = GnssNoiseModel(seed=42)
        self._noise_model.update_from_config({
            'normal_gnss_std_m':    self.get_parameter('noise.normal_gnss_std_m').value,
            'rtk_float_std_m':      self.get_parameter('noise.rtk_float_std_m').value,
            'rtk_fixed_std_m':      self.get_parameter('noise.rtk_fixed_std_m').value,
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

        self.create_subscription(
            Odometry, '/uav/ground_truth', self._ground_truth_cb, 10)
        self.create_subscription(
            NavSatFix, '/rtk/base_station', self._base_station_cb, 10)
        if self._use_l2:
            rtcm_topic = self.get_parameter('simulated_rtcm_topic').value
            self.create_subscription(SimulatedRtcm, rtcm_topic, self._rtcm_cb, 10)

        self._pub_raw_gps      = self.create_publisher(NavSatFix,         '/uav/raw_gps',        10)
        self._pub_rtk_pos      = self.create_publisher(NavSatFix,         '/uav/rtk_position',   10)
        self._pub_rtk_status   = self.create_publisher(String,            '/uav/rtk_status',     10)
        self._pub_accuracy     = self.create_publisher(Float32MultiArray, '/rtk/accuracy',        10)
        self._pub_error_metrics = self.create_publisher(Float32MultiArray, '/rtk/error_metrics',  10)

        mode = (
            'Level 2 — PX4/Gazebo integration'
            if self._use_l2 else
            'Level 1 — standalone simulation'
        )
        self.get_logger().info(
            f'RTK positioning node started — {mode}\n'
            f'  noise GNSS_ONLY={self._noise_model.get_std("GNSS_ONLY")} m  '
            f'RTK_FLOAT={self._noise_model.get_std("RTK_FLOAT")} m  '
            f'RTK_FIXED={self._noise_model.get_std("RTK_FIXED")} m'
        )

    # ------------------------------------------------------------------
    def _base_station_cb(self, msg: NavSatFix):
        self._base_lat = msg.latitude
        self._base_lon = msg.longitude
        self._base_alt = msg.altitude

    # ------------------------------------------------------------------
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

        raw_pos = self._correction_model.apply_raw_gnss(true_pos)
        rtk_pos = self._correction_model.apply_correction(true_pos, rtk_status)

        # Actual measured 3D Euclidean errors against ground truth (in meters)
        raw_error_m = float(np.linalg.norm(raw_pos - true_pos))
        rtk_error_m = float(np.linalg.norm(rtk_pos - true_pos))

        raw_lat, raw_lon, raw_alt = enu_to_wgs84(
            self._base_lat, self._base_lon, self._base_alt,
            raw_pos[0], raw_pos[1], raw_pos[2])

        rtk_lat, rtk_lon, rtk_alt = enu_to_wgs84(
            self._base_lat, self._base_lon, self._base_alt,
            rtk_pos[0], rtk_pos[1], rtk_pos[2])

        stamp   = now.to_msg()
        raw_std = self._noise_model.get_std('GNSS_ONLY')
        rtk_std = self._noise_model.get_std(rtk_status)

        self._publish_raw_gps(stamp, raw_lat, raw_lon, raw_alt, raw_std)
        self._publish_rtk_position(stamp, rtk_lat, rtk_lon, rtk_alt, rtk_std)
        self._publish_rtk_status(rtk_status, rtk_std)
        self._publish_accuracy(raw_std, rtk_std)
        self._publish_error_metrics(raw_error_m, rtk_error_m)

    # ------------------------------------------------------------------
    def _rtcm_cb(self, msg: SimulatedRtcm):
        self._latest_rtcm    = msg
        self._last_rtcm_time = self.get_clock().now()

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

    # ------------------------------------------------------------------
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


def main(args=None):
    rclpy.init(args=args)
    node = RtkPositioningNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
