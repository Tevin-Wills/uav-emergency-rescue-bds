"""
PX4/Gazebo pose adapter node for Level 2 RTK positioning simulation.

Subscribes to the Gazebo navsat sensor topic bridged into ROS 2 via ros_gz_bridge
and republishes the UAV position as a normalised nav_msgs/Odometry message on
/uav/ground_truth — the same topic the RTK positioning node already consumes.

Data path:
  Gazebo navsat sensor  (gz.msgs.NavSat, ~30 Hz)
        ↓
  ros_gz_bridge         (sensor_msgs/NavSatFix  →  /gz/navsat)
        ↓
  px4_pose_adapter_node (WGS84 → ENU via wgs84_to_enu())
        ↓
  /uav/ground_truth     (nav_msgs/Odometry, 10 Hz)
        ↓
  rtk_positioning_node  (unchanged from Level 1)

Why ros_gz_bridge instead of /fmu/out/vehicle_odometry:
  px4_msgs is not installed, so the PX4 uXRCE-DDS topics are not available
  as typed ROS 2 topics.  ros_gz_bridge is installed and directly exposes
  the Gazebo navsat sensor, which is the raw GPS signal the RTK module
  should be receiving — more appropriate than the PX4 EKF-filtered output.

The bridge must be started separately before this node receives any data.
If no data arrives within 5 seconds the node logs the exact bridge command
needed to fix the problem.

Bridge command (run in a separate terminal, after sourcing ROS 2):
  ros2 run ros_gz_bridge parameter_bridge \\
    /world/default/model/x500_1/link/base_link/sensor/navsat_sensor/navsat@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat \\
    --ros-args -r /world/default/model/x500_1/link/base_link/sensor/navsat_sensor/navsat:=/gz/navsat
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion

from rtk_positioning.coordinate_transform import wgs84_to_enu

# Watchdog: warn after this many publish cycles with no bridge data
_WATCHDOG_CYCLES = 50   # 50 × 0.1 s = 5 s


class Px4PoseAdapterNode(Node):

    def __init__(self):
        super().__init__('px4_pose_adapter_node')

        self.declare_parameter('gz_navsat_topic',  '/gz/navsat')
        self.declare_parameter('world_origin_lat', 47.397971057728981)
        self.declare_parameter('world_origin_lon',  8.5461637398001447)
        self.declare_parameter('world_origin_alt',  0.0)
        self.declare_parameter('publish_rate_hz',  10.0)

        gz_topic        = self.get_parameter('gz_navsat_topic').value
        self._base_lat  = self.get_parameter('world_origin_lat').value
        self._base_lon  = self.get_parameter('world_origin_lon').value
        self._base_alt  = self.get_parameter('world_origin_alt').value
        rate_hz         = self.get_parameter('publish_rate_hz').value

        self._latest_navsat  = None
        self._watchdog_count = 0

        self.create_subscription(NavSatFix, gz_topic, self._navsat_cb, 10)
        self._pub = self.create_publisher(Odometry, '/uav/ground_truth', 10)
        self.create_timer(1.0 / rate_hz, self._publish_cb)

        self.get_logger().info(
            f'PX4 pose adapter started\n'
            f'  subscribing to : {gz_topic}\n'
            f'  world origin   : lat={self._base_lat:.6f}  '
            f'lon={self._base_lon:.6f}  alt={self._base_alt:.1f} m\n'
            f'  publishing on  : /uav/ground_truth  at {rate_hz} Hz'
        )

    # ------------------------------------------------------------------
    def _navsat_cb(self, msg: NavSatFix):
        self._latest_navsat  = msg
        self._watchdog_count = 0        # reset watchdog on every received message

    # ------------------------------------------------------------------
    def _publish_cb(self):
        if self._latest_navsat is None:
            self._watchdog_count += 1
            if self._watchdog_count == _WATCHDOG_CYCLES:
                gz_topic = self.get_parameter('gz_navsat_topic').value
                self.get_logger().warn(
                    f'No data on {gz_topic} after 5 s.\n'
                    'Start ros_gz_bridge in a separate terminal:\n'
                    '  source /opt/ros/jazzy/setup.bash\n'
                    '  ros2 run ros_gz_bridge parameter_bridge \\\n'
                    '    /world/default/model/x500_1/link/base_link/sensor/'
                    'navsat_sensor/navsat'
                    '@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat \\\n'
                    '    --ros-args -r '
                    '/world/default/model/x500_1/link/base_link/sensor/'
                    'navsat_sensor/navsat:=/gz/navsat'
                )
            return

        nav = self._latest_navsat
        east_m, north_m, up_m = wgs84_to_enu(
            self._base_lat, self._base_lon, self._base_alt,
            nav.latitude, nav.longitude, nav.altitude,
        )

        msg = Odometry()
        msg.header.stamp            = self.get_clock().now().to_msg()
        msg.header.frame_id         = 'odom'
        msg.child_frame_id          = 'base_link'
        msg.pose.pose.position.x    = east_m
        msg.pose.pose.position.y    = north_m
        msg.pose.pose.position.z    = up_m
        msg.pose.pose.orientation   = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)

        self._pub.publish(msg)

    # ------------------------------------------------------------------
    def destroy_node(self):
        self.get_logger().info('PX4 pose adapter shut down.')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Px4PoseAdapterNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
