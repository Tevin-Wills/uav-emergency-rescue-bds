"""Image decoding and simple annotation helpers without ROS dependencies."""

from __future__ import annotations

from pathlib import Path

import numpy as np


def decode_color_image(
    *,
    height: int,
    width: int,
    encoding: str,
    step: int,
    data: bytes,
) -> np.ndarray:
    """Decode a sensor_msgs/Image-like payload into RGB uint8 HxWx3."""

    if height <= 0 or width <= 0:
        raise ValueError("Received empty color image")

    normalized = encoding.upper()
    if normalized in ("RGB8", "BGR8", "8UC3"):
        channels = 3
    elif normalized in ("RGBA8", "BGRA8", "8UC4"):
        channels = 4
    elif normalized in ("MONO8", "8UC1"):
        channels = 1
    else:
        raise ValueError(f"Unsupported color image encoding: {encoding}")

    row_width = step
    expected = row_width * height
    raw = np.frombuffer(data, dtype=np.uint8, count=expected)
    if raw.size != expected:
        raise ValueError(
            f"Color image data size mismatch: got {raw.size}, expected {expected}"
        )
    rows = raw.reshape((height, row_width))
    packed = rows[:, : width * channels].reshape((height, width, channels))

    if normalized == "BGR8":
        return packed[:, :, ::-1].copy()
    if normalized == "BGRA8":
        return packed[:, :, [2, 1, 0]].copy()
    if normalized in ("RGBA8", "8UC4"):
        return packed[:, :, :3].copy()
    if normalized in ("MONO8", "8UC1"):
        return np.repeat(packed, 3, axis=2)
    return packed.copy()


def decode_depth_image(
    *,
    height: int,
    width: int,
    encoding: str,
    step: int,
    data: bytes,
) -> np.ndarray:
    """Decode a sensor_msgs/Image-like payload into depth metres."""

    if height <= 0 or width <= 0:
        raise ValueError("Received empty depth image")

    normalized = encoding.upper()
    if normalized in ("32FC1", "32FC"):
        dtype = np.float32
        bytes_per_pixel = 4
        scale = 1.0
    elif normalized in ("16UC1", "MONO16"):
        dtype = np.uint16
        bytes_per_pixel = 2
        scale = 0.001
    else:
        raise ValueError(f"Unsupported depth image encoding: {encoding}")

    row_width = step // bytes_per_pixel
    expected = row_width * height
    raw = np.frombuffer(data, dtype=dtype, count=expected)
    if raw.size != expected:
        raise ValueError(
            f"Depth image data size mismatch: got {raw.size}, expected {expected}"
        )
    depth = raw.reshape((height, row_width))[:, :width].astype(np.float32)
    return depth * scale


def draw_rectangles_rgb(
    image_rgb: np.ndarray,
    boxes: list[list[float]],
    color: tuple[int, int, int] = (20, 220, 60),
) -> np.ndarray:
    """Draw lightweight rectangle outlines in RGB without OpenCV."""

    annotated = image_rgb.copy()
    height, width = annotated.shape[:2]
    for box in boxes:
        xmin, ymin, xmax, ymax = [int(round(value)) for value in box]
        xmin = max(0, min(width - 1, xmin))
        xmax = max(0, min(width - 1, xmax))
        ymin = max(0, min(height - 1, ymin))
        ymax = max(0, min(height - 1, ymax))
        if xmax <= xmin or ymax <= ymin:
            continue
        annotated[ymin : min(height, ymin + 2), xmin:xmax] = color
        annotated[max(0, ymax - 1) : ymax + 1, xmin:xmax] = color
        annotated[ymin:ymax, xmin : min(width, xmin + 2)] = color
        annotated[ymin:ymax, max(0, xmax - 1) : xmax + 1] = color
    return annotated


def write_ppm(path: Path, image_rgb: np.ndarray) -> None:
    """Write a binary PPM screenshot with no external image dependency."""

    if image_rgb.dtype != np.uint8 or image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
        raise ValueError("image_rgb must be uint8 HxWx3")
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"P6\n{image_rgb.shape[1]} {image_rgb.shape[0]}\n255\n".encode("ascii")
    with path.open("wb") as handle:
        handle.write(header)
        handle.write(np.ascontiguousarray(image_rgb).tobytes())
