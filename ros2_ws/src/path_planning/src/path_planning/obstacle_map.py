#!/usr/bin/env python3
"""
obstacle_map.py — synthetic obstacle grid + geodetic helpers for path_planning.

Stage-1 obstacle source: a STATIC/SYNTHETIC occupancy grid representing the
rescue area in a local metric (ENU) frame. This deliberately DECOUPLES
path_planning from the camera/Gazebo backbone (target_detection is untouched).

==============================================================================
⚠️  COMMITTED DEFERRED UPGRADE (U1) — DO NOT FORGET
    Replace `build_synthetic_grid()` with a live depth-camera -> 2D costmap
    projection once the PX4/Gazebo camera backbone is solid. The RRT* planner
    (rrt_star_planner.py) is unchanged by this swap — only the grid source
    changes. At that point path_planning and target_detection will share
    /depth_camera (two consumers, different uses; not a conflict).
    Tracked in: INTEGRATION_2DAY_PLAN.md "Committed deferred upgrades" + memory.
==============================================================================
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from path_planning.rrt_star_planner import OccupancyGridMap

# Mean Earth radius (m) for the local equirectangular projection.
_EARTH_RADIUS_M = 6371000.0


def build_synthetic_grid(
    width_m: float = 100.0,
    height_m: float = 100.0,
    resolution: float = 1.0,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    walls: Sequence[Tuple[float, float, float, float]] = None,
    occupied_threshold: int = 30,
) -> OccupancyGridMap:
    """Build a static obstacle grid in the local metric frame.

    walls: list of (x_min, y_min, x_max, y_max) rectangles in metres marked
    occupied. Defaults to a small "collapsed-structure" layout (a few walls
    with gaps) inspired by the contributed Gazebo worlds, so the RRT* planner
    has something non-trivial to route around.
    """
    n_cols = int(round(width_m / resolution))
    n_rows = int(round(height_m / resolution))
    cells: List[List[int]] = [[0 for _ in range(n_cols)] for _ in range(n_rows)]

    if walls is None:
        # Default earthquake-zone-style layout: two offset walls forming an
        # S-corridor that the straight line cannot use, forcing a detour.
        # Tuned (C2) so the real rescue goal (~datum +60 m E / +90 m N) and the
        # start (~datum origin) both fall in FREE space and a path exists.
        # NOTE: synthetic/illustrative only — replaced by a live depth costmap at U1.
        walls = [
            (25.0, 0.0, 30.0, 75.0),     # lower wall, gap above y=75
            (50.0, 40.0, 55.0, 100.0),   # upper wall, gap below y=40 (forces an S-route)
        ]

    grid = OccupancyGridMap(
        cells=cells, origin_x=origin_x, origin_y=origin_y,
        resolution=resolution, occupied_threshold=occupied_threshold,
    )
    for (xmin, ymin, xmax, ymax) in walls:
        _fill_rect(grid, xmin, ymin, xmax, ymax, value=100)
    return grid


def _fill_rect(grid: OccupancyGridMap, xmin, ymin, xmax, ymax, value=100):
    c0, r0 = grid.world_to_cell(xmin, ymin)
    c1, r1 = grid.world_to_cell(xmax, ymax)
    c0, c1 = sorted((max(0, c0), min(grid.width - 1, c1)))
    r0, r1 = sorted((max(0, r0), min(grid.height - 1, r1)))
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid.cells[r][c] = value


# ---- geodetic helpers: WGS-84 lat/lon <-> local ENU metres ----------------
def latlon_to_local(lat: float, lon: float, lat0: float, lon0: float):
    """Equirectangular projection of (lat,lon) to local ENU metres about a datum.

    Good to <1 m over the few-hundred-metre rescue area we plan in.
    Returns (east_x, north_y).
    """
    lat0_rad = math.radians(lat0)
    x = math.radians(lon - lon0) * _EARTH_RADIUS_M * math.cos(lat0_rad)
    y = math.radians(lat - lat0) * _EARTH_RADIUS_M
    return x, y


def local_to_latlon(x: float, y: float, lat0: float, lon0: float):
    """Inverse of latlon_to_local. Returns (lat, lon)."""
    lat0_rad = math.radians(lat0)
    lat = lat0 + math.degrees(y / _EARTH_RADIUS_M)
    lon = lon0 + math.degrees(x / (_EARTH_RADIUS_M * math.cos(lat0_rad)))
    return lat, lon
