"""Coordinate helpers shared by ROS1/ROS2 wrappers."""

from __future__ import annotations

from dataclasses import dataclass
import math


METERS_PER_DEG_LAT = 111320.0


@dataclass(frozen=True)
class PlatformPose:
    """UAV pose in PX4 local NED plus a heading angle."""

    north_m: float
    east_m: float
    down_m: float
    heading_rad: float

    @property
    def up_m(self) -> float:
        return -self.down_m


def camera_xyz_to_local_ned(
    body_xyz_m: tuple[float, float, float],
    pose: PlatformPose,
) -> tuple[float, float, float]:
    """Transform body x-forward/y-left/z-up into local NED metres."""

    forward_m, left_m, up_m = body_xyz_m
    cos_h = math.cos(pose.heading_rad)
    sin_h = math.sin(pose.heading_rad)

    north_offset_m = cos_h * forward_m + sin_h * left_m
    east_offset_m = sin_h * forward_m - cos_h * left_m
    down_offset_m = -up_m
    return (
        pose.north_m + north_offset_m,
        pose.east_m + east_offset_m,
        pose.down_m + down_offset_m,
    )


def local_ned_to_enu(ned_m: tuple[float, float, float]) -> tuple[float, float, float]:
    north_m, east_m, down_m = ned_m
    return east_m, north_m, -down_m


def enu_offset_to_wgs84(
    base_lat_deg: float,
    base_lon_deg: float,
    base_alt_m: float,
    east_m: float,
    north_m: float,
    up_m: float,
) -> tuple[float, float, float]:
    lat = base_lat_deg + north_m / METERS_PER_DEG_LAT
    lon_scale = METERS_PER_DEG_LAT * math.cos(math.radians(base_lat_deg))
    lon = base_lon_deg + east_m / lon_scale
    alt = base_alt_m + up_m
    return lat, lon, alt
