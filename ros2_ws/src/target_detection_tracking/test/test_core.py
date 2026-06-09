import math

import numpy as np

from target_detection_tracking.core import (
    BoundingBox,
    CameraModel,
    DepthRoiConfig,
    DepthTargetPipeline,
    Detection,
    camera_xyz_from_bbox_depth,
    median_depth_for_bbox,
)
from target_detection_tracking.image_utils import decode_color_image, decode_depth_image
from target_detection_tracking.transforms import PlatformPose, camera_xyz_to_local_ned


def test_decode_color_image_bgr8_to_rgb():
    bgr = np.array(
        [
            [[3, 2, 1], [6, 5, 4]],
            [[9, 8, 7], [12, 11, 10]],
        ],
        dtype=np.uint8,
    )

    rgb = decode_color_image(
        height=2,
        width=2,
        encoding="bgr8",
        step=6,
        data=bgr.tobytes(),
    )

    assert rgb.tolist() == [
        [[1, 2, 3], [4, 5, 6]],
        [[7, 8, 9], [10, 11, 12]],
    ]


def test_decode_depth_image_32fc1_with_row_step():
    row_major = np.array(
        [
            [1.0, 2.0, 99.0],
            [3.0, 4.0, 99.0],
        ],
        dtype=np.float32,
    )

    depth = decode_depth_image(
        height=2,
        width=2,
        encoding="32FC1",
        step=12,
        data=row_major.tobytes(),
    )

    np.testing.assert_allclose(depth, np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))


def test_median_depth_for_bbox_scales_rgb_bbox_to_depth_roi():
    depth = np.array(
        [
            [1.0, 2.0, 3.0, 4.0],
            [5.0, 6.0, 7.0, 8.0],
            [9.0, 10.0, 11.0, 12.0],
            [13.0, 14.0, 15.0, 16.0],
        ],
        dtype=np.float32,
    )
    bbox = BoundingBox(0.0, 0.0, 8.0, 8.0)
    config = DepthRoiConfig(
        x_margin_fraction=0.25,
        y_start_fraction=0.25,
        y_end_fraction=0.75,
        min_depth_m=0.1,
        max_depth_m=20.0,
        min_valid_ratio=0.1,
    )

    result = median_depth_for_bbox(depth, bbox, rgb_shape=(8, 8), roi_config=config)

    assert result is not None
    median_m, valid_ratio = result
    assert median_m == 8.5
    assert valid_ratio == 1.0


def test_camera_xyz_from_bbox_depth_uses_project_convention():
    camera = CameraModel(
        rgb_width=4,
        rgb_height=4,
        rgb_horizontal_fov_rad=math.pi / 2.0,
    )
    bbox = BoundingBox(1.0, 1.0, 3.0, 3.0)

    xyz = camera_xyz_from_bbox_depth(
        bbox,
        depth_m=4.0,
        camera=camera,
        rgb_shape=(4, 4),
    )

    np.testing.assert_allclose(xyz, (4.0, -1.0, -1.6), atol=1e-6)


def test_camera_body_to_local_ned_heading_zero():
    pose = PlatformPose(north_m=10.0, east_m=20.0, down_m=-3.0, heading_rad=0.0)

    local_ned = camera_xyz_to_local_ned((5.0, 2.0, 1.0), pose)

    np.testing.assert_allclose(local_ned, (15.0, 18.0, -4.0), atol=1e-6)


def test_pipeline_keeps_stable_track_id_for_repeated_target():
    pipeline = DepthTargetPipeline(
        camera=CameraModel(
            rgb_width=4,
            rgb_height=4,
            rgb_horizontal_fov_rad=math.pi / 2.0,
        ),
        roi_config=DepthRoiConfig(
            x_margin_fraction=0.0,
            y_start_fraction=0.0,
            y_end_fraction=1.0,
            min_depth_m=0.1,
            max_depth_m=20.0,
            min_valid_ratio=0.1,
        ),
    )
    detection = Detection(
        label="person",
        confidence=0.9,
        bbox=BoundingBox(1.0, 1.0, 3.0, 3.0),
    )
    depth = np.full((4, 4), 4.0, dtype=np.float32)
    pose = PlatformPose(north_m=0.0, east_m=0.0, down_m=0.0, heading_rad=0.0)

    first = pipeline.localize([detection], rgb_shape=(4, 4), depth_m=depth, platform_pose=pose)
    second = pipeline.localize([detection], rgb_shape=(4, 4), depth_m=depth, platform_pose=pose)

    assert first[0].track_id == 1
    assert second[0].track_id == 1
