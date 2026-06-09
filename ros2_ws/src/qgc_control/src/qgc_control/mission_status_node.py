#!/usr/bin/env python3
"""
mission_status_node.py — Stage-1 integration stub for qgc_control.

Drives the rescue mission state machine and broadcasts it to the whole system.
Starts IDLE; when a BeiDou distress coordinate arrives it walks the mission
through its phases on a dwell timer, jumping to TARGET_ACQUIRED early if
target_detection reports a hit.

Publishes:
  /mission/status     (std_msgs/String)   -- current phase (consumed by all modules)
  /mission/waypoints  (nav_msgs/Path)      -- waypoints toward the rescue coordinate

Subscribes:
  /target/emergency_coordinate (interfaces/EmergencyCoordinate) -- mission trigger
  /target/detection            (std_msgs/Bool)                  -- early TARGET_ACQUIRED

PX4 bridge note: this stub does NOT command PX4. For the Stage-1 demo, flight is
via PX4 mission mode; the MAVROS path is in uav_control_node.py (deferred decision,
see interfaces/integration_contract.md Reconciliation Log [C]).
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from std_msgs.msg import String, Bool, Header
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from interfaces.msg import EmergencyCoordinate

# Phase sequence walked once a distress coordinate is received.
PHASES = [
    "DISTRESS_RECEIVED",
    "MISSION_PLANNED",
    "IN_FLIGHT",
    "TARGET_ACQUIRED",
    "LANDING",
    "COMPLETE",
]


class MissionStatusNode(Node):

    def __init__(self):
        super().__init__("mission_status_node")

        self.declare_parameter("phase_dwell_sec", 5.0)
        self._dwell = float(self.get_parameter("phase_dwell_sec").value)

        self._phase = "IDLE"
        self._phase_idx = -1          # index into PHASES once started
        self._coord = None            # EmergencyCoordinate
        self._time_in_phase = 0.0

        latched = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
        )

        self._pub_status = self.create_publisher(String, "/mission/status", 10)
        self._pub_wps = self.create_publisher(Path, "/mission/waypoints", latched)

        self.create_subscription(
            EmergencyCoordinate, "/target/emergency_coordinate",
            self._on_coordinate, latched)
        self.create_subscription(
            Bool, "/target/detection", self._on_detection, 10)

        # 1 Hz: broadcast current phase + advance the state machine.
        self._tick_period = 1.0
        self.create_timer(self._tick_period, self._tick)
        self.get_logger().info("mission_status_node up; waiting for distress coordinate (phase IDLE).")

    # ---- callbacks -------------------------------------------------------
    def _on_coordinate(self, msg: EmergencyCoordinate):
        if self._coord is not None:
            return
        self._coord = msg
        self.get_logger().info(
            f"Distress coordinate received (lat={msg.latitude:.4f}, lon={msg.longitude:.4f}); "
            "starting mission.")
        self._publish_waypoints(msg)
        self._enter_phase(0)

    def _on_detection(self, msg: Bool):
        # Jump straight to TARGET_ACQUIRED on a positive detection while in flight.
        if msg.data and self._phase == "IN_FLIGHT":
            self.get_logger().info("Target detected -> TARGET_ACQUIRED.")
            self._enter_phase(PHASES.index("TARGET_ACQUIRED"))

    # ---- state machine ---------------------------------------------------
    def _enter_phase(self, idx: int):
        self._phase_idx = idx
        self._phase = PHASES[idx]
        self._time_in_phase = 0.0
        self.get_logger().info(f"Mission phase -> {self._phase}")

    def _tick(self):
        status = String(data=self._phase)
        self._pub_status.publish(status)

        if self._phase in ("IDLE", "COMPLETE"):
            return

        self._time_in_phase += self._tick_period
        if self._time_in_phase >= self._dwell and self._phase_idx < len(PHASES) - 1:
            self._enter_phase(self._phase_idx + 1)

    def _publish_waypoints(self, coord: EmergencyCoordinate):
        # Minimal stub path: single goal pose at the rescue coordinate, in a
        # lat/lon frame. path_planning refines this into an obstacle-free path.
        path = Path()
        path.header = Header(frame_id="wgs84", stamp=self.get_clock().now().to_msg())
        goal = PoseStamped()
        goal.header = path.header
        goal.pose.position.x = coord.longitude
        goal.pose.position.y = coord.latitude
        goal.pose.position.z = 0.0
        goal.pose.orientation.w = 1.0
        path.poses = [goal]
        self._pub_wps.publish(path)


def main(args=None):
    rclpy.init(args=args)
    node = MissionStatusNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
