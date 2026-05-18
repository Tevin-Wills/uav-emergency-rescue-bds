"""
Simulated UAV node for Level 1 RTK positioning simulation.

Generates a repeatable square-search movement path and publishes
the UAV ground-truth position as nav_msgs/Odometry on /uav/ground_truth.

Path legs (default 50 m, 5 m/s):
  Leg 1 — East
  Leg 2 — North
  Leg 3 — West
  Leg 4 — South
  Then repeats.

This node does not require PX4, Gazebo, or any hardware.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


class SimulatedUavNode(Node):

    def __init__(self):
        super().__init__('simulated_uav_node')

        self.declare_parameter('publish_rate_hz', 10.0)
        self.declare_parameter('leg_length_m',    50.0)
        self.declare_parameter('speed_m_s',        5.0)
        self.declare_parameter('flight_altitude_m', 30.0)

        rate          = self.get_parameter('publish_rate_hz').value
        self._leg_m   = self.get_parameter('leg_length_m').value
        self._speed   = self.get_parameter('speed_m_s').value
        self._alt_agl = self.get_parameter('flight_altitude_m').value

        self._pub = self.create_publisher(Odometry, '/uav/ground_truth', 10)
        self.create_timer(1.0 / rate, self._publish)
        self._start_time = None

        self.get_logger().info(
            f'Simulated UAV node started — '
            f'square path, leg={self._leg_m} m, speed={self._speed} m/s'
        )

    def _square_position(self, elapsed_sec):
        """Return ENU (x, y, z) meters for a square-search path at elapsed time."""
        leg_duration = self._leg_m / self._speed
        cycle = elapsed_sec % (4.0 * leg_duration)
        t = cycle / leg_duration

        if t < 1.0:
            x, y = t * self._leg_m, 0.0
        elif t < 2.0:
            x, y = self._leg_m, (t - 1.0) * self._leg_m
        elif t < 3.0:
            x, y = (3.0 - t) * self._leg_m, self._leg_m
        else:
            x, y = 0.0, (4.0 - t) * self._leg_m

        return x, y, self._alt_agl

    def _publish(self):
        now = self.get_clock().now()
        if self._start_time is None:
            self._start_time = now

        elapsed = (now - self._start_time).nanoseconds * 1e-9
        x, y, z = self._square_position(elapsed)

        msg = Odometry()
        msg.header.stamp    = now.to_msg()
        msg.header.frame_id = 'map'
        msg.child_frame_id  = 'uav_base_link'
        msg.pose.pose.position.x  = x
        msg.pose.pose.position.y  = y
        msg.pose.pose.position.z  = z
        msg.pose.pose.orientation.w = 1.0
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SimulatedUavNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
