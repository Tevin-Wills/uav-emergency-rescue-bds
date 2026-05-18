"""
Base station node for Level 1 RTK positioning simulation.

Publishes the fixed RTK base station coordinate at 1 Hz.
The base station is stationary throughout the simulation.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus


class BaseStationNode(Node):

    def __init__(self):
        super().__init__('base_station_node')

        self.declare_parameter('base_station.latitude',  39.981000)
        self.declare_parameter('base_station.longitude', 116.344000)
        self.declare_parameter('base_station.altitude',  50.0)
        self.declare_parameter('base_station.frame_id',  'base_station')

        self._lat      = self.get_parameter('base_station.latitude').value
        self._lon      = self.get_parameter('base_station.longitude').value
        self._alt      = self.get_parameter('base_station.altitude').value
        self._frame_id = self.get_parameter('base_station.frame_id').value

        self._pub = self.create_publisher(NavSatFix, '/rtk/base_station', 10)
        self.create_timer(1.0, self._publish)

        self.get_logger().info(
            f'Base station node started — '
            f'lat={self._lat}, lon={self._lon}, alt={self._alt} m'
        )

    def _publish(self):
        msg = NavSatFix()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id
        msg.status.status  = NavSatStatus.STATUS_FIX
        msg.status.service = NavSatStatus.SERVICE_GPS
        msg.latitude  = self._lat
        msg.longitude = self._lon
        msg.altitude  = self._alt
        msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = BaseStationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
