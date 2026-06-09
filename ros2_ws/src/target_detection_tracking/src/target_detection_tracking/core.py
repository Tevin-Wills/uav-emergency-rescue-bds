"""ROS-agnostic target detection, tracking, and depth geolocation core.

The simulation runtime uses the PX4 Gazebo Oak-D Lite model as RGB plus depth:
YOLO detects a person in the RGB image, the matching depth ROI estimates range,
and the camera-frame point is transformed into the UAV local frame.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np

from target_detection_tracking.tracking import HybridTrackManager
from target_detection_tracking.transforms import (
    PlatformPose,
    camera_xyz_to_local_ned,
    enu_offset_to_wgs84,
    local_ned_to_enu,
)


@dataclass(frozen=True)
class BoundingBox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    @classmethod
    def from_xyxy(cls, values: Iterable[float]) -> "BoundingBox":
        xmin, ymin, xmax, ymax = [float(value) for value in values]
        return cls(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)

    @property
    def width(self) -> float:
        return max(0.0, self.xmax - self.xmin)

    @property
    def height(self) -> float:
        return max(0.0, self.ymax - self.ymin)

    @property
    def center(self) -> tuple[float, float]:
        return (self.xmin + self.xmax) * 0.5, (self.ymin + self.ymax) * 0.5

    def as_xyxy(self) -> list[float]:
        return [self.xmin, self.ymin, self.xmax, self.ymax]


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float | None
    bbox: BoundingBox
    image_track_id: int | None = None


@dataclass(frozen=True)
class CameraModel:
    rgb_width: int = 640
    rgb_height: int = 360
    depth_width: int = 320
    depth_height: int = 240
    rgb_horizontal_fov_rad: float = 1.204
    mount_x_forward_m: float = 0.12
    mount_y_left_m: float = 0.03
    mount_z_up_m: float = 0.242

    @property
    def fx_px(self) -> float:
        return self.rgb_width / (2.0 * np.tan(self.rgb_horizontal_fov_rad * 0.5))

    @property
    def fy_px(self) -> float:
        return self.fx_px

    @property
    def cx_px(self) -> float:
        return (self.rgb_width - 1.0) * 0.5

    @property
    def cy_px(self) -> float:
        return (self.rgb_height - 1.0) * 0.5

    @property
    def mount_xyz_m(self) -> tuple[float, float, float]:
        return (
            self.mount_x_forward_m,
            self.mount_y_left_m,
            self.mount_z_up_m,
        )


@dataclass(frozen=True)
class DepthRoiConfig:
    x_margin_fraction: float = 0.30
    y_start_fraction: float = 0.30
    y_end_fraction: float = 0.85
    min_depth_m: float = 0.20
    max_depth_m: float = 19.10
    min_valid_ratio: float = 0.05


@dataclass
class LocalizedTarget:
    label: str
    confidence: float | None
    bbox_xyxy: list[float]
    depth_m: float
    depth_valid_ratio: float
    camera_xyz_m: tuple[float, float, float]
    body_xyz_m: tuple[float, float, float]
    local_ned_m: tuple[float, float, float] | None
    local_enu_m: tuple[float, float, float] | None
    global_llh: tuple[float, float, float] | None
    image_track_id: int | None = None
    track_id: int | None = None
    track_source: str | None = None

    def to_record(self) -> dict:
        record = asdict(self)
        record["camera_xyz_m"] = list(self.camera_xyz_m)
        record["body_xyz_m"] = list(self.body_xyz_m)
        record["local_ned_m"] = list(self.local_ned_m) if self.local_ned_m else None
        record["local_enu_m"] = list(self.local_enu_m) if self.local_enu_m else None
        record["global_llh"] = list(self.global_llh) if self.global_llh else None
        return record


@dataclass(frozen=True)
class RtkFix:
    latitude_deg: float
    longitude_deg: float
    altitude_m: float
    status_text: str | None = None
    horizontal_error_m: float | None = None


def _scaled_bbox_to_depth_roi(
    bbox: BoundingBox,
    rgb_shape: tuple[int, int],
    depth_shape: tuple[int, int],
    roi_config: DepthRoiConfig,
) -> tuple[int, int, int, int]:
    rgb_h, rgb_w = rgb_shape
    depth_h, depth_w = depth_shape
    scale_x = depth_w / max(1.0, float(rgb_w))
    scale_y = depth_h / max(1.0, float(rgb_h))

    xmin = bbox.xmin * scale_x
    xmax = bbox.xmax * scale_x
    ymin = bbox.ymin * scale_y
    ymax = bbox.ymax * scale_y
    width = xmax - xmin
    height = ymax - ymin

    x0 = int(max(0, xmin + roi_config.x_margin_fraction * width))
    x1 = int(min(depth_w, xmax - roi_config.x_margin_fraction * width))
    y0 = int(max(0, ymin + roi_config.y_start_fraction * height))
    y1 = int(min(depth_h, ymin + roi_config.y_end_fraction * height))
    return x0, y0, x1, y1


def median_depth_for_bbox(
    depth_m: np.ndarray,
    bbox: BoundingBox,
    rgb_shape: tuple[int, int],
    roi_config: DepthRoiConfig,
) -> tuple[float, float] | None:
    """Return median depth and valid-pixel ratio for a detection bbox."""

    if depth_m.ndim != 2:
        raise ValueError("depth_m must be a single-channel image")
    x0, y0, x1, y1 = _scaled_bbox_to_depth_roi(
        bbox,
        rgb_shape=rgb_shape,
        depth_shape=depth_m.shape,
        roi_config=roi_config,
    )
    if x1 <= x0 or y1 <= y0:
        return None

    roi = depth_m[y0:y1, x0:x1]
    valid = roi[np.isfinite(roi)]
    valid = valid[
        (valid >= roi_config.min_depth_m)
        & (valid <= roi_config.max_depth_m)
    ]
    valid_ratio = float(valid.size / max(1, roi.size))
    if valid.size == 0 or valid_ratio < roi_config.min_valid_ratio:
        return None
    return float(np.median(valid)), valid_ratio


def camera_xyz_from_bbox_depth(
    bbox: BoundingBox,
    depth_m: float,
    camera: CameraModel,
    rgb_shape: tuple[int, int],
) -> tuple[float, float, float]:
    """Project a target point into project camera coordinates.

    Coordinates follow the existing target_detection convention:
    x forward, y left, z up.
    """

    image_h, image_w = rgb_shape
    width_scale = camera.rgb_width / max(1.0, float(image_w))
    height_scale = camera.rgb_height / max(1.0, float(image_h))

    u_raw, _ = bbox.center
    v_raw = bbox.ymin + 0.65 * bbox.height
    u = u_raw * width_scale
    v = v_raw * height_scale

    x_forward = float(depth_m)
    x_right = (u - camera.cx_px) * x_forward / camera.fx_px
    y_down = (v - camera.cy_px) * x_forward / camera.fy_px
    return (x_forward, -float(x_right), -float(y_down))


def add_camera_mount_offset(
    camera_xyz_m: tuple[float, float, float],
    camera: CameraModel,
) -> tuple[float, float, float]:
    return tuple(
        float(camera_xyz_m[index] + camera.mount_xyz_m[index])
        for index in range(3)
    )


class DepthTargetPipeline:
    """Run depth geolocation and stable ID assignment for detections."""

    def __init__(
        self,
        camera: CameraModel | None = None,
        roi_config: DepthRoiConfig | None = None,
        tracker: HybridTrackManager | None = None,
    ):
        self.camera = camera or CameraModel()
        self.roi_config = roi_config or DepthRoiConfig()
        self.tracker = tracker or HybridTrackManager()

    def localize(
        self,
        detections: list[Detection],
        rgb_shape: tuple[int, int],
        depth_m: np.ndarray,
        platform_pose: PlatformPose | None,
        rtk_fix: RtkFix | None = None,
    ) -> list[LocalizedTarget]:
        targets: list[LocalizedTarget] = []

        for detection in detections:
            depth_result = median_depth_for_bbox(
                depth_m,
                detection.bbox,
                rgb_shape=rgb_shape,
                roi_config=self.roi_config,
            )
            if depth_result is None:
                continue

            depth_value_m, valid_ratio = depth_result
            camera_xyz = camera_xyz_from_bbox_depth(
                detection.bbox,
                depth_value_m,
                self.camera,
                rgb_shape=rgb_shape,
            )
            body_xyz = add_camera_mount_offset(camera_xyz, self.camera)

            local_ned = None
            local_enu = None
            global_llh = None
            if platform_pose is not None:
                local_ned = camera_xyz_to_local_ned(body_xyz, platform_pose)
                local_enu = local_ned_to_enu(local_ned)
                if rtk_fix is not None:
                    global_llh = enu_offset_to_wgs84(
                        rtk_fix.latitude_deg,
                        rtk_fix.longitude_deg,
                        rtk_fix.altitude_m,
                        local_enu[0] - platform_pose.east_m,
                        local_enu[1] - platform_pose.north_m,
                        local_enu[2] - platform_pose.up_m,
                    )

            targets.append(
                LocalizedTarget(
                    label=detection.label,
                    confidence=detection.confidence,
                    bbox_xyxy=detection.bbox.as_xyxy(),
                    depth_m=depth_value_m,
                    depth_valid_ratio=valid_ratio,
                    camera_xyz_m=camera_xyz,
                    body_xyz_m=body_xyz,
                    local_ned_m=local_ned,
                    local_enu_m=local_enu,
                    global_llh=global_llh,
                    image_track_id=detection.image_track_id,
                )
            )

        world_positions = [
            target.local_enu_m if target.local_enu_m is not None else target.camera_xyz_m
            for target in targets
        ]
        self.tracker.update(targets, world_positions)
        return targets


def closest_target(targets: list[LocalizedTarget]) -> LocalizedTarget | None:
    if not targets:
        return None
    return min(targets, key=lambda target: target.depth_m)
