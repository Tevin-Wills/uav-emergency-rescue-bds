#!/usr/bin/env python3
"""
mission_status_node.py — Stage-1 integration stub for qgc_control.

Drives the rescue mission state machine and broadcasts it to the whole system.
Starts IDLE; when a BeiDou distress coordinate arrives it walks the mission
through its phases on a dwell timer, jumping to TARGET_ACQUIRED early if
target_detection reports a hit.

RTK-gated precision landing (resilient-RTK integration):
  The LANDING decision is gated on RTK positioning quality.
  - /rtk/mission_viability (String) GATES the decision: the drone only descends
    to a precision landing when viability == LANDING_VIABLE. Otherwise it enters
    LANDING_HOLD (hover) and waits for RTK to re-converge; if it does not recover
    within landing_hold_timeout_sec, the mission goes to ABORTED.
  - /uav/rtk_status (String) INFORMS: its fix type + accuracy are logged so the
    demo shows *why* it is holding (e.g. "LANDING_HOLD — RTK_FLOAT, 0.80 m").
  This realises the resilient-RTK story end-to-end and closes the Level 3
  report's open gap (precision-landing re-convergence).

Publishes:
  /mission/status     (std_msgs/String)   -- current phase (consumed by all modules)
  /mission/waypoints  (nav_msgs/Path)      -- waypoints toward the rescue coordinate

Subscribes:
  /target/emergency_coordinate (interfaces/EmergencyCoordinate) -- mission trigger
  /target/detection            (std_msgs/Bool)                  -- early TARGET_ACQUIRED
  /rtk/mission_viability       (std_msgs/String)                -- landing gate (L3)
  /uav/rtk_status              (std_msgs/String)                -- fix type + accuracy (informs)

Fallback: if no viability is received (e.g. stubs-only demo, use_rtk:=false) and
require_viability is False (default), landing proceeds as before so the
control-plane demo still completes.

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

# Linear phase sequence auto-advanced on the dwell timer, up to LANDING.
# LANDING is then gated on RTK viability; COMPLETE / LANDING_HOLD / ABORTED are
# reached via the gate logic, not auto-advance.
PHASES = [
    "DISTRESS_RECEIVED",
    "MISSION_PLANNED",
    "IN_FLIGHT",
    "TARGET_ACQUIRED",
    "LANDING",
]


class MissionStatusNode(Node):

    def __init__(self):
        super().__init__("mission_status_node")

        self.declare_parameter("phase_dwell_sec", 5.0)
        self.declare_parameter("require_viability", False)
        self.declare_parameter("landing_hold_timeout_sec", 30.0)
        self._dwell = float(self.get_parameter("phase_dwell_sec").value)
        self._require_viability = bool(self.get_parameter("require_viability").value)
        self._hold_timeout = float(self.get_parameter("landing_hold_timeout_sec").value)

        self._phase = "IDLE"
        self._coord = None            # EmergencyCoordinate
        self._time_in_phase = 0.0
        self._viability = None        # latest /rtk/mission_viability
        self._rtk_status = None       # latest /uav/rtk_status (display)

        latched = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
        )

        self._pub_status = self.create_publisher(String, "/mission/status", 10)
        self._pub_wps = self.create_publisher(Path, "/mission/waypoints", latched)
        # C3: aggregated operator telemetry (contract output; feeds the dashboard).
        self._pub_telemetry = self.create_publisher(String, "/uav/telemetry", 10)

        self.create_subscription(
            EmergencyCoordinate, "/target/emergency_coordinate",
            self._on_coordinate, latched)
        self.create_subscription(Bool, "/target/detection", self._on_detection, 10)
        self.create_subscription(String, "/rtk/mission_viability", self._on_viability, 10)
        self.create_subscription(String, "/uav/rtk_status", self._on_rtk_status, 10)

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
        self._set_phase("DISTRESS_RECEIVED")

    def _on_detection(self, msg: Bool):
        if msg.data and self._phase == "IN_FLIGHT":
            self.get_logger().info("Target detected -> TARGET_ACQUIRED.")
            self._set_phase("TARGET_ACQUIRED")

    def _on_viability(self, msg: String):
        self._viability = msg.data

    def _on_rtk_status(self, msg: String):
        self._rtk_status = msg.data

    # ---- state machine ---------------------------------------------------
    def _set_phase(self, name: str):
        self._phase = name
        self._time_in_phase = 0.0
        self.get_logger().info(f"Mission phase -> {name}")

    def _rtk_reason(self) -> str:
        """Human-readable RTK context for logs (status informs)."""
        v = self._viability if self._viability is not None else "no-viability"
        if self._rtk_status:
            # /uav/rtk_status format: "<code>|<name>|<accuracy_m>"
            parts = self._rtk_status.split("|")
            name = parts[1] if len(parts) > 1 else self._rtk_status
            acc = f", {float(parts[2]):.2f} m" if len(parts) > 2 else ""
            return f"{v} ({name}{acc})"
        return v

    def _can_land(self) -> bool:
        """Gate on /rtk/mission_viability == LANDING_VIABLE."""
        if self._viability is None:
            # No RTK viability yet: permissive unless strict mode is requested.
            return not self._require_viability
        return self._viability == "LANDING_VIABLE"

    def _tick(self):
        self._pub_status.publish(String(data=self._phase))
        # C3: aggregated telemetry (phase + RTK quality) for operator/dashboard.
        self._pub_telemetry.publish(
            String(data=f"phase={self._phase}; rtk={self._rtk_reason()}"))

        if self._phase in ("IDLE", "COMPLETE", "ABORTED"):
            return

        self._time_in_phase += self._tick_period

        if self._phase == "LANDING":
            self._tick_landing()
        elif self._phase == "LANDING_HOLD":
            self._tick_landing_hold()
        else:
            # Linear approach phases: auto-advance on dwell.
            if self._time_in_phase >= self._dwell:
                nxt = PHASES[PHASES.index(self._phase) + 1]
                self._set_phase(nxt)

    def _tick_landing(self):
        # Arrived at the landing point (after dwell): attempt precision landing.
        if self._time_in_phase < self._dwell:
            return
        if self._can_land():
            self.get_logger().info(f"Landing cleared ({self._rtk_reason()}); descending -> COMPLETE.")
            self._set_phase("COMPLETE")
        else:
            self.get_logger().warn(f"Landing blocked by RTK ({self._rtk_reason()}); holding.")
            self._set_phase("LANDING_HOLD")

    def _tick_landing_hold(self):
        if self._can_land():
            self.get_logger().info(f"RTK recovered ({self._rtk_reason()}); descending -> COMPLETE.")
            self._set_phase("COMPLETE")
        elif self._time_in_phase >= self._hold_timeout:
            self.get_logger().error(
                f"RTK did not recover within {self._hold_timeout:.0f}s ({self._rtk_reason()}); "
                "aborting landing.")
            self._set_phase("ABORTED")
        elif int(self._time_in_phase) % 5 == 0:
            self.get_logger().warn(f"LANDING_HOLD — waiting for RTK ({self._rtk_reason()}).")

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
