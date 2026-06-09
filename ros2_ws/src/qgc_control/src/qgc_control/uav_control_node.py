#!/usr/bin/env python3
"""
Task 2: UAV Control Node
Project: UAV Emergency Rescue System based on BeiDou Navigation
This code implements the UAV Control Node, which is responsible for autonomous mission execution.
It communicates with the flight controller through MAVROS, receives GNSS and camera data, uploads waypoints, arms the drone, and supervises the mission.
Author: (UWASE YVONNE)
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import NavSatFix, Image
from mavros_msgs.msg import State, Waypoint
from mavros_msgs.srv import CommandBool, SetMode, WaypointPush, WaypointClear

import cv2
import os

try:
    from cv_bridge import CvBridge
    CV_BRIDGE_AVAILABLE = True
except ImportError:
    CV_BRIDGE_AVAILABLE = False

# Drone spawn location
HOME_LAT = 47.3979709
HOME_LON = 8.5461649

# Waypoints close to home (within 500m)
WAYPOINTS = [
    (47.3979709, 8.5461649, 30.0),
    (47.3984709, 8.5461649, 30.0),
    (47.3984709, 8.5471649, 30.0),
    (47.3979709, 8.5471649, 30.0),
    (47.3979709, 8.5461649, 30.0),
]
TAKEOFF_ALTITUDE = 30.0
IMAGE_SAVE_DIR = os.path.expanduser("~/uav_images")


class UAVControlNode(Node):

    STEP_WAIT_CONNECTION = 0
    STEP_CLEAR_MISSION   = 1
    STEP_UPLOAD_MISSION  = 2
    STEP_SET_MODE        = 3
    STEP_ARM             = 4
    STEP_FLYING          = 5

    def __init__(self):
        super().__init__("uav_control_node")
        self.get_logger().info("UAV Control Node starting...")
        os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)

        self.current_state = State()
        self.current_gnss  = None
        self.image_count   = 0
        self.step          = self.STEP_WAIT_CONNECTION
        self.pending       = None

        if CV_BRIDGE_AVAILABLE:
            self.bridge = CvBridge()
        else:
            self.bridge = None
            self.get_logger().warning("cv_bridge not found")

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.create_subscription(State,     "/mavros/state",                  self.state_cb, 10)
        self.create_subscription(NavSatFix, "/mavros/global_position/global", self.gnss_cb,  sensor_qos)
        self.create_subscription(Image,     "/camera/image_raw",              self.image_cb, sensor_qos)

        self.arm_client  = self.create_client(CommandBool,   "/mavros/cmd/arming")
        self.mode_client = self.create_client(SetMode,       "/mavros/set_mode")
        self.wp_clear    = self.create_client(WaypointClear, "/mavros/mission/clear")
        self.wp_push     = self.create_client(WaypointPush,  "/mavros/mission/push")

        self.create_timer(1.0, self.control_loop)
        self.get_logger().info("Waiting for FCU connection...")

    def state_cb(self, msg):
        self.current_state = msg

    def gnss_cb(self, msg):
        self.current_gnss = msg
        self.get_logger().info(
            f"[GNSS] lat={msg.latitude:.7f}  lon={msg.longitude:.7f}  "
            f"alt={msg.altitude:.2f} m  fix={msg.status.status}"
        )

    def image_cb(self, msg):
        if not self.bridge:
            return
        try:
            frame    = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            filename = os.path.join(IMAGE_SAVE_DIR, f"frame_{self.image_count:05d}.jpg")
            cv2.imwrite(filename, frame)
            self.image_count += 1
            self.get_logger().info(f"[CAM] Saved {filename}")
        except Exception as e:
            self.get_logger().warning(f"[CAM] {e}")

    def call_service(self, client, request):
        if not client.service_is_ready():
            self.get_logger().warning(f"Service not ready: {client.srv_name}")
            return False
        self.pending = client.call_async(request)
        return True

    def pending_done(self):
        if self.pending is None:
            return True
        if self.pending.done():
            self.pending = None
            return True
        return False

    def control_loop(self):
        if not self.pending_done():
            return

        if self.step == self.STEP_WAIT_CONNECTION:
            if self.current_state.connected:
                self.get_logger().info("FCU connected! Clearing old mission...")
                self.step = self.STEP_CLEAR_MISSION
            return

        if self.step == self.STEP_CLEAR_MISSION:
            if self.call_service(self.wp_clear, WaypointClear.Request()):
                self.step = self.STEP_UPLOAD_MISSION
            return

        if self.step == self.STEP_UPLOAD_MISSION:
            wp_list = []

            home              = Waypoint()
            home.frame        = Waypoint.FRAME_GLOBAL_REL_ALT
            home.command      = 22
            home.is_current   = True
            home.autocontinue = True
            home.x_lat        = HOME_LAT
            home.y_long       = HOME_LON
            home.z_alt        = TAKEOFF_ALTITUDE
            wp_list.append(home)

            for lat, lon, alt in WAYPOINTS:
                wp              = Waypoint()
                wp.frame        = Waypoint.FRAME_GLOBAL_REL_ALT
                wp.command      = 16
                wp.is_current   = False
                wp.autocontinue = True
                wp.x_lat        = lat
                wp.y_long       = lon
                wp.z_alt        = alt
                wp_list.append(wp)

            req             = WaypointPush.Request()
            req.start_index = 0
            req.waypoints   = wp_list

            if self.call_service(self.wp_push, req):
                self.get_logger().info(f"Uploading {len(wp_list)} waypoints to FCU...")
                self.step = self.STEP_SET_MODE
            return

        if self.step == self.STEP_SET_MODE:
            if self.current_state.mode == "AUTO.MISSION":
                self.get_logger().info("Mode confirmed: AUTO.MISSION")
                self.step = self.STEP_ARM
                return
            self.get_logger().info("Setting AUTO.MISSION mode...")
            req             = SetMode.Request()
            req.custom_mode = "AUTO.MISSION"
            self.call_service(self.mode_client, req)
            return

        if self.step == self.STEP_ARM:
            if self.current_state.armed:
                self.get_logger().info("Drone ARMED — mission started!")
                self.step = self.STEP_FLYING
                return
            self.get_logger().info("Arming drone...")
            req       = CommandBool.Request()
            req.value = True
            self.call_service(self.arm_client, req)
            return

        if self.step == self.STEP_FLYING:
            if self.current_gnss:
                self.get_logger().info(
                    f"[MISSION ACTIVE] "
                    f"lat={self.current_gnss.latitude:.6f}  "
                    f"lon={self.current_gnss.longitude:.6f}  "
                    f"alt={self.current_gnss.altitude:.1f} m | "
                    f"images saved={self.image_count}"
                )


def main(args=None):
    rclpy.init(args=args)
    node = UAVControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
