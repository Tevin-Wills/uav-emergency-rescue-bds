"""ROS 2 adapter for the middleware-independent target detection core."""

from __future__ import annotations

import json
from pathlib import Path
import time

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image, NavSatFix
from std_msgs.msg import Bool, String

from px4_msgs.msg import VehicleLocalPosition

from target_detection_tracking.core import (
    CameraModel,
    DepthRoiConfig,
    DepthTargetPipeline,
    RtkFix,
    closest_target,
)
from target_detection_tracking.detector import YoloPersonDetector
from target_detection_tracking.image_utils import (
    decode_color_image,
    decode_depth_image,
    draw_rectangles_rgb,
    write_ppm,
)
from target_detection_tracking.tracking import HybridTrackManager
from target_detection_tracking.transforms import PlatformPose


def _default_model_path() -> str:
    share_dir = Path(get_package_share_directory("target_detection_tracking"))
    return str(share_dir / "models" / "kitti_person_yolov8n_best.pt")


def _default_results_root() -> Path:
    share_dir = Path(get_package_share_directory("target_detection_tracking")).resolve()
    for parent in [share_dir, *share_dir.parents]:
        if parent.name == "uav-emergency-rescue-bds":
            return parent / "results"
    return Path.cwd() / "results"


class TargetDetectionNode(Node):
    """Detect a simulated rescue target and publish standard ROS topics."""

    def __init__(self):
        super().__init__("target_detection_node")

        self.declare_parameter("model_path", "")
        self.declare_parameter("rgb_topic", "/camera/image_raw")
        self.declare_parameter("depth_topic", "/depth_camera")
        self.declare_parameter("local_position_topic", "/fmu/out/vehicle_local_position")
        self.declare_parameter("rtk_position_topic", "/uav/rtk_position")
        self.declare_parameter("rtk_status_topic", "/uav/rtk_status")
        self.declare_parameter("mission_status_topic", "/mission/status")
        self.declare_parameter("confidence_threshold", 0.25)
        self.declare_parameter("process_every_n_frames", 1)
        self.declare_parameter("max_image_skew_sec", 0.35)
        self.declare_parameter("depth_timeout_sec", 0.75)
        self.declare_parameter("pose_timeout_sec", 1.50)
        self.declare_parameter("require_local_pose", True)
        self.declare_parameter("active_without_mission_status", True)
        self.declare_parameter(
            "active_mission_phases",
            ["IN_FLIGHT", "TARGET_ACQUIRED", "LANDING"],
        )
        self.declare_parameter("publish_frame_id", "px4_local_enu")
        self.declare_parameter("enable_jsonl_log", True)
        self.declare_parameter("enable_screenshots", True)
        self.declare_parameter("screenshot_interval_sec", 10.0)
        self.declare_parameter("results_root", "")
        self.declare_parameter("rgb_width", 640)
        self.declare_parameter("rgb_height", 360)
        self.declare_parameter("depth_width", 320)
        self.declare_parameter("depth_height", 240)
        self.declare_parameter("rgb_horizontal_fov_rad", 1.204)
        self.declare_parameter("camera_mount_x_forward_m", 0.12)
        self.declare_parameter("camera_mount_y_left_m", 0.03)
        self.declare_parameter("camera_mount_z_up_m", 0.242)
        self.declare_parameter("roi_x_margin_fraction", 0.30)
        self.declare_parameter("roi_y_start_fraction", 0.30)
        self.declare_parameter("roi_y_end_fraction", 0.85)
        self.declare_parameter("min_depth_m", 0.20)
        self.declare_parameter("max_depth_m", 19.10)
        self.declare_parameter("min_depth_valid_ratio", 0.05)
        self.declare_parameter("track_iou_threshold", 0.25)
        self.declare_parameter("track_max_missing", 12)
        self.declare_parameter("track_position_distance_m", 4.0)

        model_path = str(self.get_parameter("model_path").value).strip() or _default_model_path()
        self._rgb_topic = str(self.get_parameter("rgb_topic").value)
        self._depth_topic = str(self.get_parameter("depth_topic").value)
        self._frame_id = str(self.get_parameter("publish_frame_id").value)
        self._process_every_n_frames = max(
            1, int(self.get_parameter("process_every_n_frames").value)
        )
        self._max_image_skew = Duration(
            seconds=float(self.get_parameter("max_image_skew_sec").value)
        )
        self._depth_timeout = Duration(
            seconds=float(self.get_parameter("depth_timeout_sec").value)
        )
        self._pose_timeout = Duration(
            seconds=float(self.get_parameter("pose_timeout_sec").value)
        )
        self._require_local_pose = bool(self.get_parameter("require_local_pose").value)
        self._active_without_mission_status = bool(
            self.get_parameter("active_without_mission_status").value
        )
        self._active_phases = {
            str(value).upper()
            for value in self.get_parameter("active_mission_phases").value
        }
        self._enable_jsonl_log = bool(self.get_parameter("enable_jsonl_log").value)
        self._enable_screenshots = bool(self.get_parameter("enable_screenshots").value)
        self._screenshot_interval_sec = float(
            self.get_parameter("screenshot_interval_sec").value
        )
        results_root_raw = str(self.get_parameter("results_root").value).strip()
        self._results_root = Path(results_root_raw) if results_root_raw else _default_results_root()
        self._screenshot_dir = self._results_root / "screenshots" / "target_detection_tracking"
        self._log_path = self._results_root / "logs" / "target_detection_tracking" / "detections.jsonl"

        camera = CameraModel(
            rgb_width=int(self.get_parameter("rgb_width").value),
            rgb_height=int(self.get_parameter("rgb_height").value),
            depth_width=int(self.get_parameter("depth_width").value),
            depth_height=int(self.get_parameter("depth_height").value),
            rgb_horizontal_fov_rad=float(
                self.get_parameter("rgb_horizontal_fov_rad").value
            ),
            mount_x_forward_m=float(
                self.get_parameter("camera_mount_x_forward_m").value
            ),
            mount_y_left_m=float(self.get_parameter("camera_mount_y_left_m").value),
            mount_z_up_m=float(self.get_parameter("camera_mount_z_up_m").value),
        )
        roi = DepthRoiConfig(
            x_margin_fraction=float(
                self.get_parameter("roi_x_margin_fraction").value
            ),
            y_start_fraction=float(
                self.get_parameter("roi_y_start_fraction").value
            ),
            y_end_fraction=float(self.get_parameter("roi_y_end_fraction").value),
            min_depth_m=float(self.get_parameter("min_depth_m").value),
            max_depth_m=float(self.get_parameter("max_depth_m").value),
            min_valid_ratio=float(self.get_parameter("min_depth_valid_ratio").value),
        )
        tracker = HybridTrackManager(
            iou_threshold=float(self.get_parameter("track_iou_threshold").value),
            max_missing=int(self.get_parameter("track_max_missing").value),
            position_distance_threshold_m=float(
                self.get_parameter("track_position_distance_m").value
            ),
        )
        self._pipeline = DepthTargetPipeline(
            camera=camera,
            roi_config=roi,
            tracker=tracker,
        )
        self._detector = YoloPersonDetector(
            model_path=model_path,
            confidence=float(self.get_parameter("confidence_threshold").value),
        )

        self._latest_rgb = None
        self._latest_rgb_stamp = None
        self._latest_rgb_msg_stamp = None
        self._latest_depth = None
        self._latest_depth_stamp = None
        self._latest_pose: PlatformPose | None = None
        self._latest_pose_stamp = None
        self._latest_rtk: RtkFix | None = None
        self._latest_rtk_status = None
        self._latest_mission_phase = None
        self._frames_seen = 0
        self._last_screenshot_monotonic = 0.0
        self._detector_error_reported = False

        px4_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.create_subscription(Image, self._rgb_topic, self._rgb_cb, 10)
        self.create_subscription(Image, self._depth_topic, self._depth_cb, 10)
        self.create_subscription(
            VehicleLocalPosition,
            str(self.get_parameter("local_position_topic").value),
            self._local_position_cb,
            px4_qos,
        )
        self.create_subscription(
            NavSatFix,
            str(self.get_parameter("rtk_position_topic").value),
            self._rtk_cb,
            10,
        )
        self.create_subscription(
            String,
            str(self.get_parameter("rtk_status_topic").value),
            self._rtk_status_cb,
            10,
        )
        self.create_subscription(
            String,
            str(self.get_parameter("mission_status_topic").value),
            self._mission_status_cb,
            10,
        )

        self._detection_pub = self.create_publisher(Bool, "/target/detection", 10)
        self._location_pub = self.create_publisher(PoseStamped, "/target/location", 10)

        self.get_logger().info(
            "Target detection node started\n"
            f"  model_path={model_path}\n"
            f"  rgb_topic={self._rgb_topic}\n"
            f"  depth_topic={self._depth_topic}\n"
            f"  publish_frame_id={self._frame_id}\n"
            f"  results_root={self._results_root}"
        )

    def _rgb_cb(self, msg: Image):
        try:
            self._latest_rgb = decode_color_image(
                height=msg.height,
                width=msg.width,
                encoding=msg.encoding,
                step=msg.step,
                data=msg.data,
            )
        except ValueError as exc:
            self.get_logger().warn(str(exc), throttle_duration_sec=2.0)
            return
        self._latest_rgb_stamp = self.get_clock().now()
        self._latest_rgb_msg_stamp = msg.header.stamp
        self._try_process()

    def _depth_cb(self, msg: Image):
        try:
            self._latest_depth = decode_depth_image(
                height=msg.height,
                width=msg.width,
                encoding=msg.encoding,
                step=msg.step,
                data=msg.data,
            )
        except ValueError as exc:
            self.get_logger().warn(str(exc), throttle_duration_sec=2.0)
            return
        self._latest_depth_stamp = self.get_clock().now()

    def _local_position_cb(self, msg: VehicleLocalPosition):
        if not (msg.xy_valid and msg.z_valid):
            return
        self._latest_pose = PlatformPose(
            north_m=float(msg.x),
            east_m=float(msg.y),
            down_m=float(msg.z),
            heading_rad=float(msg.heading),
        )
        self._latest_pose_stamp = self.get_clock().now()

    def _rtk_cb(self, msg: NavSatFix):
        horizontal_error = None
        cov = list(msg.position_covariance)
        if len(cov) >= 5 and cov[0] >= 0.0 and cov[4] >= 0.0:
            horizontal_error = float(max(cov[0], cov[4]) ** 0.5)
        self._latest_rtk = RtkFix(
            latitude_deg=float(msg.latitude),
            longitude_deg=float(msg.longitude),
            altitude_m=float(msg.altitude),
            status_text=self._latest_rtk_status,
            horizontal_error_m=horizontal_error,
        )

    def _rtk_status_cb(self, msg: String):
        self._latest_rtk_status = msg.data
        if self._latest_rtk is not None:
            self._latest_rtk = RtkFix(
                latitude_deg=self._latest_rtk.latitude_deg,
                longitude_deg=self._latest_rtk.longitude_deg,
                altitude_m=self._latest_rtk.altitude_m,
                status_text=msg.data,
                horizontal_error_m=self._latest_rtk.horizontal_error_m,
            )

    def _mission_status_cb(self, msg: String):
        text = msg.data.strip()
        if "|" in text:
            text = text.split("|")[-1].strip()
        self._latest_mission_phase = text.upper()

    def _is_active(self) -> bool:
        if self._latest_mission_phase is None:
            return self._active_without_mission_status
        return self._latest_mission_phase in self._active_phases

    def _inputs_ready(self) -> bool:
        now = self.get_clock().now()
        if self._latest_rgb is None or self._latest_rgb_stamp is None:
            return False
        if self._latest_depth is None or self._latest_depth_stamp is None:
            self.get_logger().warn("Waiting for depth image", throttle_duration_sec=2.0)
            return False
        if now - self._latest_depth_stamp > self._depth_timeout:
            self.get_logger().warn("Depth image is stale", throttle_duration_sec=2.0)
            return False
        if abs((self._latest_rgb_stamp - self._latest_depth_stamp).nanoseconds) > self._max_image_skew.nanoseconds:
            self.get_logger().warn("RGB/depth image timestamps are too far apart", throttle_duration_sec=2.0)
            return False
        if self._require_local_pose:
            if self._latest_pose is None or self._latest_pose_stamp is None:
                self.get_logger().warn("Waiting for local vehicle pose", throttle_duration_sec=2.0)
                return False
            if now - self._latest_pose_stamp > self._pose_timeout:
                self.get_logger().warn("Local vehicle pose is stale", throttle_duration_sec=2.0)
                return False
        return True

    def _try_process(self):
        self._frames_seen += 1
        if self._frames_seen % self._process_every_n_frames != 0:
            return
        if not self._is_active():
            self._detection_pub.publish(Bool(data=False))
            return
        if not self._inputs_ready():
            self._detection_pub.publish(Bool(data=False))
            return

        try:
            detections = self._detector.detect(self._latest_rgb)
        except Exception as exc:  # noqa: BLE001 - keep the ROS node alive.
            if not self._detector_error_reported:
                self.get_logger().error(f"Detector unavailable: {exc}")
                self._detector_error_reported = True
            self._detection_pub.publish(Bool(data=False))
            return

        rgb_shape = self._latest_rgb.shape[:2]
        targets = self._pipeline.localize(
            detections=detections,
            rgb_shape=rgb_shape,
            depth_m=self._latest_depth,
            platform_pose=self._latest_pose,
            rtk_fix=self._latest_rtk,
        )
        target = closest_target(targets)
        detected = target is not None
        self._detection_pub.publish(Bool(data=bool(detected)))

        if detected and target.local_enu_m is not None:
            self._publish_location(target)
            self._maybe_write_screenshot(targets)
        self._write_log(detections, targets)

    def _publish_location(self, target):
        east_m, north_m, up_m = target.local_enu_m
        msg = PoseStamped()
        msg.header.stamp = self._latest_rgb_msg_stamp
        msg.header.frame_id = self._frame_id
        msg.pose.position.x = float(east_m)
        msg.pose.position.y = float(north_m)
        msg.pose.position.z = float(up_m)
        msg.pose.orientation.w = 1.0
        self._location_pub.publish(msg)

    def _maybe_write_screenshot(self, targets):
        if not self._enable_screenshots or not targets:
            return
        now = time.monotonic()
        if (
            self._screenshot_interval_sec > 0.0
            and now - self._last_screenshot_monotonic < self._screenshot_interval_sec
        ):
            return
        self._last_screenshot_monotonic = now
        boxes = [target.bbox_xyxy for target in targets]
        annotated = draw_rectangles_rgb(self._latest_rgb, boxes)
        stamp_ns = self.get_clock().now().nanoseconds
        path = self._screenshot_dir / f"target_detection_{stamp_ns}.ppm"
        try:
            write_ppm(path, annotated)
        except OSError as exc:
            self.get_logger().warn(f"Could not write screenshot {path}: {exc}")

    def _write_log(self, detections, targets):
        if not self._enable_jsonl_log:
            return
        row = {
            "stamp_ns": self.get_clock().now().nanoseconds,
            "mission_phase": self._latest_mission_phase,
            "rtk_status": self._latest_rtk_status,
            "detections": [
                {
                    "label": item.label,
                    "confidence": item.confidence,
                    "bbox_xyxy": item.bbox.as_xyxy(),
                    "image_track_id": item.image_track_id,
                }
                for item in detections
            ],
            "targets": [target.to_record() for target in targets],
        }
        try:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
        except OSError as exc:
            self.get_logger().warn(f"Could not write detection log: {exc}", throttle_duration_sec=5.0)


def main(args=None):
    rclpy.init(args=args)
    node = TargetDetectionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
