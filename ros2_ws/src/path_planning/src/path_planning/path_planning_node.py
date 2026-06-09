#!/usr/bin/env python3
"""
path_planning_node.py — RRT* obstacle-avoidance planner (Stage-1, synthetic grid).

Replaces the earlier straight-line stub. Runs the salvaged RRT* planner
(rrt_star_planner.py, derived from px4_rrt_avoidance / PythonRobotics) over a
static synthetic obstacle grid (obstacle_map.py) and publishes an obstacle-free
path.

Publishes:
  /map/obstacles  (nav_msgs/OccupancyGrid)  -- the obstacle field (frame "map"), latched
  /planner/path   (nav_msgs/Path)           -- RRT* path through it (frame "map")

Subscribes (integration wiring — gates planning on the live mission):
  /mission/status              (std_msgs/String)              -- only plan in active phases
  /target/emergency_coordinate (interfaces/EmergencyCoordinate) -- distress trigger
  /uav/rtk_position            (sensor_msgs/NavSatFix)        -- UAV position (logged)

FRAME NOTE (Stage-1, synthetic): the planner runs in a LOCAL metric frame
("map", metres). start/goal are parameters in that frame, NOT real lat/lon,
because the modules are currently geographically inconsistent (BeiDou sample =
Hangzhou; PX4/Gazebo home + QGC waypoints = Zurich). Reconciling a single datum/
home across all modules is a separate integration issue. Geodetic helpers
(obstacle_map.latlon_to_local) are ready for when that is fixed.

⚠️ DEFERRED UPGRADE U1: synthetic grid -> live depth-camera costmap once the
   Gazebo backbone is solid (see obstacle_map.py + INTEGRATION_2DAY_PLAN.md).
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from std_msgs.msg import String, Header
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Path, OccupancyGrid
from geometry_msgs.msg import PoseStamped
from interfaces.msg import EmergencyCoordinate

from path_planning.rrt_star_planner import RRTStar
from path_planning import obstacle_map

ACTIVE_PHASES = {"MISSION_PLANNED", "IN_FLIGHT", "TARGET_ACQUIRED", "LANDING"}


class PathPlanningNode(Node):

    def __init__(self):
        super().__init__("path_planning_node")

        # --- parameters ---
        self.declare_parameter("map_width_m", 100.0)
        self.declare_parameter("map_height_m", 100.0)
        self.declare_parameter("map_resolution_m", 1.0)
        self.declare_parameter("start_xy", [5.0, 5.0])
        self.declare_parameter("goal_xy", [95.0, 95.0])
        self.declare_parameter("replan_period_sec", 2.0)
        self.declare_parameter("rrt_max_iter", 3000)
        self.declare_parameter("rrt_seed", 1)
        self.declare_parameter("require_distress", True)
        # Shared datum (from bringup/config/datum.yaml; defaults = Zurich). Used by
        # obstacle_map.latlon_to_local to convert RTK/goal lat/lon into the local
        # planning frame once a single datum is shared across modules (real-frame
        # planning; today the node plans with parameterized local endpoints).
        self.declare_parameter("datum_lat", 47.397971057728981)
        self.declare_parameter("datum_lon", 8.5461637398001447)
        self._datum_lat = float(self.get_parameter("datum_lat").value)
        self._datum_lon = float(self.get_parameter("datum_lon").value)

        w = float(self.get_parameter("map_width_m").value)
        h = float(self.get_parameter("map_height_m").value)
        res = float(self.get_parameter("map_resolution_m").value)
        self._start = list(self.get_parameter("start_xy").value)
        self._goal = list(self.get_parameter("goal_xy").value)
        self._require_distress = bool(self.get_parameter("require_distress").value)

        # --- synthetic obstacle grid + planner ---
        self._grid = obstacle_map.build_synthetic_grid(
            width_m=w, height_m=h, resolution=res)
        self._planner = RRTStar(
            self._grid,
            max_iter=int(self.get_parameter("rrt_max_iter").value),
            seed=int(self.get_parameter("rrt_seed").value),
        )

        # --- state ---
        self._phase = "IDLE"
        self._have_distress = False

        latched = QoSProfile(
            depth=1, reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL, history=HistoryPolicy.KEEP_LAST)

        self._pub_grid = self.create_publisher(OccupancyGrid, "/map/obstacles", latched)
        self._pub_path = self.create_publisher(Path, "/planner/path", 10)

        self.create_subscription(String, "/mission/status", self._on_phase, 10)
        self.create_subscription(
            EmergencyCoordinate, "/target/emergency_coordinate", self._on_distress, latched)
        self.create_subscription(NavSatFix, "/uav/rtk_position", self._on_rtk, 10)

        self._publish_grid()
        self.create_timer(float(self.get_parameter("replan_period_sec").value), self._replan)
        self.get_logger().info(
            f"path_planning_node up: RRT* on {self._grid.width}x{self._grid.height} synthetic grid "
            f"(start {self._start} -> goal {self._goal}, frame 'map').")

    # ---- callbacks -------------------------------------------------------
    def _on_phase(self, msg: String):
        self._phase = msg.data

    def _on_distress(self, msg: EmergencyCoordinate):
        if not self._have_distress:
            self.get_logger().info("Distress coordinate received; planner armed.")
        self._have_distress = True

    def _on_rtk(self, msg: NavSatFix):
        # Logged for integration wiring; not used as a planning endpoint in
        # synthetic mode (see FRAME NOTE). Becomes the live start with U1.
        pass

    # ---- planning --------------------------------------------------------
    def _replan(self):
        if self._phase not in ACTIVE_PHASES:
            return
        if self._require_distress and not self._have_distress:
            return

        path = self._planner.plan(self._start, self._goal)
        if path is None:
            self.get_logger().warn("RRT* found no path this cycle; retrying next tick.")
            return
        self._publish_path(path)

    def _publish_path(self, path):
        header = Header(frame_id="map", stamp=self.get_clock().now().to_msg())
        msg = Path()
        msg.header = header
        for (x, y) in path:
            p = PoseStamped()
            p.header = header
            p.pose.position.x = float(x)
            p.pose.position.y = float(y)
            p.pose.position.z = 0.0
            p.pose.orientation.w = 1.0
            msg.poses.append(p)
        self._pub_path.publish(msg)
        self.get_logger().info(f"Published RRT* path with {len(path)} waypoints.")

    def _publish_grid(self):
        g = self._grid
        msg = OccupancyGrid()
        msg.header = Header(frame_id="map", stamp=self.get_clock().now().to_msg())
        msg.info.resolution = float(g.resolution)
        msg.info.width = g.width
        msg.info.height = g.height
        msg.info.origin.position.x = float(g.origin_x)
        msg.info.origin.position.y = float(g.origin_y)
        msg.info.origin.orientation.w = 1.0
        # Row-major, row 0 first (matches OccupancyGridMap.cells indexing).
        data = []
        for row in g.cells:
            data.extend(int(v) for v in row)
        msg.data = data
        self._pub_grid.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = PathPlanningNode()
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
