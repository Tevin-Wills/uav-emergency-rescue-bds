"""
Logger node for Level 1 RTK positioning simulation.

Subscribes to all Level 1 output topics and writes timestamped CSV logs
to results/logs/rtk_positioning/level1/.

Each run creates a new file named by wall-clock start time so previous
logs are never overwritten.

CSV columns:
  ros_time_sec,
  ground_truth_x, ground_truth_y, ground_truth_z,
  raw_gnss_lat, raw_gnss_lon, raw_gnss_alt,
  rtk_lat, rtk_lon, rtk_alt,
  raw_gnss_error_m, rtk_error_m,
  raw_gnss_std_m, rtk_std_m, improvement_pct,
  rtk_status_code, rtk_status_name, rtk_accuracy_m
"""

import csv
import os
from datetime import datetime

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import String, Float32MultiArray
from ament_index_python.packages import get_package_share_directory


def _find_default_log_dir():
    """Locate the repo results/ directory by searching up from the installed share path."""
    try:
        share_dir = get_package_share_directory('rtk_positioning')
        path = share_dir
        for _ in range(10):
            if os.path.isdir(os.path.join(path, 'results')):
                return os.path.join(
                    path, 'results', 'logs', 'rtk_positioning', 'level1')
            path = os.path.dirname(path)
    except Exception:
        pass
    # Fallback: assume standard repo location relative to home
    return os.path.join(
        os.path.expanduser('~'),
        'uav-emergency-rescue-bds', 'results', 'logs', 'rtk_positioning', 'level1'
    )


class LoggerNode(Node):

    _CSV_HEADER = [
        'ros_time_sec',
        'ground_truth_x', 'ground_truth_y', 'ground_truth_z',
        'raw_gnss_lat', 'raw_gnss_lon', 'raw_gnss_alt',
        'rtk_lat', 'rtk_lon', 'rtk_alt',
        'raw_gnss_error_m', 'rtk_error_m',
        'raw_gnss_std_m', 'rtk_std_m', 'improvement_pct',
        'rtk_status_code', 'rtk_status_name', 'rtk_accuracy_m',
    ]

    def __init__(self):
        super().__init__('logger_node')

        self.declare_parameter('log_directory', '')
        log_dir = self.get_parameter('log_directory').value
        if not log_dir:
            log_dir = _find_default_log_dir()

        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_path  = os.path.join(log_dir, f'rtk_level1_{timestamp}.csv')

        self._csv_file   = open(log_path, 'w', newline='')
        self._csv_writer = csv.writer(self._csv_file)
        self._csv_writer.writerow(self._CSV_HEADER)
        self._csv_file.flush()

        # Cached latest values — updated as topics arrive
        self._ground_truth = None
        self._raw_gps      = None
        self._rtk_pos      = None
        self._rtk_status   = '1|GNSS_ONLY|1.5000'
        self._accuracy     = [1.5, 1.5, 0.0]      # [raw_std, rtk_std, improvement]
        self._error_metrics = [0.0, 0.0]           # [raw_gnss_error_m, rtk_error_m]

        self.create_subscription(Odometry,          '/uav/ground_truth',   self._gt_cb,           10)
        self.create_subscription(NavSatFix,         '/uav/raw_gps',        self._raw_gps_cb,      10)
        self.create_subscription(NavSatFix,         '/uav/rtk_position',   self._rtk_pos_cb,      10)
        self.create_subscription(String,            '/uav/rtk_status',     self._status_cb,       10)
        self.create_subscription(Float32MultiArray, '/rtk/accuracy',       self._accuracy_cb,     10)
        self.create_subscription(Float32MultiArray, '/rtk/error_metrics',  self._error_metrics_cb, 10)

        self.get_logger().info(f'Logger node started — writing to: {log_path}')

    # ------------------------------------------------------------------
    def _gt_cb(self, msg: Odometry):
        self._ground_truth = msg
        self._write_row()

    def _raw_gps_cb(self, msg: NavSatFix):
        self._raw_gps = msg

    def _rtk_pos_cb(self, msg: NavSatFix):
        self._rtk_pos = msg

    def _status_cb(self, msg: String):
        self._rtk_status = msg.data

    def _accuracy_cb(self, msg: Float32MultiArray):
        self._accuracy = list(msg.data)

    def _error_metrics_cb(self, msg: Float32MultiArray):
        self._error_metrics = list(msg.data)

    # ------------------------------------------------------------------
    def _write_row(self):
        if self._ground_truth is None:
            return

        gt  = self._ground_truth
        raw = self._raw_gps
        rtk = self._rtk_pos

        ros_time = gt.header.stamp.sec + gt.header.stamp.nanosec * 1e-9
        gt_x = gt.pose.pose.position.x
        gt_y = gt.pose.pose.position.y
        gt_z = gt.pose.pose.position.z

        raw_lat = raw.latitude  if raw else ''
        raw_lon = raw.longitude if raw else ''
        raw_alt = raw.altitude  if raw else ''
        rtk_lat = rtk.latitude  if rtk else ''
        rtk_lon = rtk.longitude if rtk else ''
        rtk_alt = rtk.altitude  if rtk else ''

        # Actual measured errors from /rtk/error_metrics
        raw_err = self._error_metrics[0] if len(self._error_metrics) > 0 else ''
        rtk_err = self._error_metrics[1] if len(self._error_metrics) > 1 else ''

        # Model-based accuracy from /rtk/accuracy
        raw_std     = self._accuracy[0] if len(self._accuracy) > 0 else ''
        rtk_std     = self._accuracy[1] if len(self._accuracy) > 1 else ''
        improvement = self._accuracy[2] if len(self._accuracy) > 2 else ''

        # RTK status from /uav/rtk_status
        parts       = self._rtk_status.split('|')
        status_code = parts[0] if len(parts) > 0 else ''
        status_name = parts[1] if len(parts) > 1 else ''
        rtk_acc     = parts[2] if len(parts) > 2 else ''

        def fmt_f(v, decimals):
            return f'{v:.{decimals}f}' if v != '' else ''

        self._csv_writer.writerow([
            fmt_f(ros_time, 4),
            fmt_f(gt_x, 4), fmt_f(gt_y, 4), fmt_f(gt_z, 4),
            fmt_f(raw_lat, 8), fmt_f(raw_lon, 8), fmt_f(raw_alt, 4),
            fmt_f(rtk_lat, 8), fmt_f(rtk_lon, 8), fmt_f(rtk_alt, 4),
            fmt_f(raw_err, 4), fmt_f(rtk_err, 4),
            fmt_f(raw_std, 4), fmt_f(rtk_std, 4), fmt_f(improvement, 2),
            status_code, status_name, rtk_acc,
        ])
        self._csv_file.flush()

    # ------------------------------------------------------------------
    def destroy_node(self):
        self._csv_file.close()
        self.get_logger().info('Logger node shut down — CSV file closed.')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = LoggerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
