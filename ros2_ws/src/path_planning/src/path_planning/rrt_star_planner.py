#!/usr/bin/env python3
"""
rrt_star_planner.py — ROS-agnostic RRT* planner on a 2D occupancy grid.

SALVAGE PROVENANCE
------------------
The RRT* algorithm here is derived from Atsushi Sakai's PythonRobotics RRT*
(MIT License, Copyright (c) 2016-2021 Atsushi Sakai), via the contributed
ROS 1 package `px4_rrt_avoidance` (nodes/local_planner.py). That package was
ROS 1 / catkin / MAVROS / Gazebo-Classic and could not build in this ROS 2
Jazzy project. We lifted the *algorithm and grid-collision logic* and gave it a
clean interface (the occupancy grid is passed in, not a global), discarding the
rospy/MAVROS/octomap plumbing. See ros2_ws/src/path_planning/reference/ for the
original source, and interfaces/integration_contract.md for the integration role.

The planner works purely in a local metric frame (metres). World <-> grid
conversion and any lat/lon projection are the caller's responsibility (see
obstacle_map.py and path_planning_node.py).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Sequence


@dataclass
class OccupancyGridMap:
    """Minimal 2D occupancy grid in a local metric frame.

    cells[row][col]: 0 = free, 100 = occupied, -1 = unknown (treated as free).
    origin_x/origin_y: world (metre) coordinates of cell (row=0, col=0) lower-left.
    resolution: metres per cell.
    A cell is an obstacle when its value >= occupied_threshold.
    """

    cells: List[List[int]]
    origin_x: float
    origin_y: float
    resolution: float
    occupied_threshold: int = 30

    @property
    def height(self) -> int:
        return len(self.cells)

    @property
    def width(self) -> int:
        return len(self.cells[0]) if self.cells else 0

    def world_to_cell(self, x: float, y: float):
        col = int((x - self.origin_x) / self.resolution)
        row = int((y - self.origin_y) / self.resolution)
        return col, row

    def in_bounds_world(self, x: float, y: float) -> bool:
        col, row = self.world_to_cell(x, y)
        return 0 <= col < self.width and 0 <= row < self.height

    def is_occupied_world(self, x: float, y: float) -> bool:
        col, row = self.world_to_cell(x, y)
        if not (0 <= col < self.width and 0 <= row < self.height):
            # Out of the known map: treat as free (unknown space assumed clear),
            # matching the contributed planner's behaviour.
            return False
        return self.cells[row][col] >= self.occupied_threshold


class RRTStar:
    """RRT* path planning on an OccupancyGridMap, in metres.

    Faithful to the PythonRobotics RRT* structure (steer / choose_parent /
    rewire / find_near_nodes / search_best_goal_node / generate_final_course),
    with collision checking against the occupancy grid.
    """

    class Node:
        def __init__(self, x: float, y: float):
            self.x = x
            self.y = y
            self.cost = 0.0
            self.path_x: List[float] = []
            self.path_y: List[float] = []
            self.parent: Optional["RRTStar.Node"] = None

    def __init__(
        self,
        grid: OccupancyGridMap,
        expand_dis: float = 6.0,
        path_resolution: float = 1.5,
        goal_sample_rate: int = 20,
        max_iter: int = 500,
        connect_circle_dist: float = 7.0,
        seed: Optional[int] = None,
    ):
        self.grid = grid
        self.expand_dis = expand_dis
        self.path_resolution = path_resolution
        self.goal_sample_rate = goal_sample_rate
        self.max_iter = max_iter
        self.connect_circle_dist = connect_circle_dist
        self._rng = random.Random(seed)

        # Sampling bounds in world metres, shrunk one cell off each edge.
        r = grid.resolution
        self.min_x = grid.origin_x + r
        self.max_x = grid.origin_x + (grid.width - 1) * r
        self.min_y = grid.origin_y + r
        self.max_y = grid.origin_y + (grid.height - 1) * r

        self.node_list: List[RRTStar.Node] = []
        self.start: Optional[RRTStar.Node] = None
        self.end: Optional[RRTStar.Node] = None

    # ---- public API ------------------------------------------------------
    def plan(self, start_xy: Sequence[float], goal_xy: Sequence[float],
             search_until_max_iter: bool = False) -> Optional[List[List[float]]]:
        """Return a path [[x,y], ...] from start to goal (start first), or None."""
        self.start = self.Node(start_xy[0], start_xy[1])
        self.end = self.Node(goal_xy[0], goal_xy[1])
        self.node_list = [self.start]

        for _ in range(self.max_iter):
            rnd = self._get_random_node()
            nearest_ind = self._get_nearest_node_index(self.node_list, rnd)
            new_node = self._steer(self.node_list[nearest_ind], rnd, self.expand_dis)
            near_node = self.node_list[nearest_ind]
            new_node.cost = near_node.cost + math.hypot(
                new_node.x - near_node.x, new_node.y - near_node.y)

            if self._check_collision(new_node):
                near_inds = self._find_near_nodes(new_node)
                updated = self._choose_parent(new_node, near_inds)
                if updated:
                    self._rewire(updated, near_inds)
                    self.node_list.append(updated)
                else:
                    self.node_list.append(new_node)

                if not search_until_max_iter:
                    last = self._search_best_goal_node()
                    if last is not None:
                        return self._generate_final_course(last)

        last = self._search_best_goal_node()
        if last is not None:
            return self._generate_final_course(last)
        return None

    # ---- internals (faithful to PythonRobotics RRT*) ---------------------
    def _get_random_node(self) -> "RRTStar.Node":
        if self._rng.randint(0, 100) > self.goal_sample_rate:
            return self.Node(self._rng.uniform(self.min_x, self.max_x),
                             self._rng.uniform(self.min_y, self.max_y))
        return self.Node(self.end.x, self.end.y)

    def _steer(self, from_node, to_node, extend_length=float("inf")):
        new_node = self.Node(from_node.x, from_node.y)
        d, theta = self._calc_distance_and_angle(new_node, to_node)
        new_node.path_x = [new_node.x]
        new_node.path_y = [new_node.y]

        extend_length = min(extend_length, d)
        n_expand = int(math.floor(extend_length / self.path_resolution))
        for _ in range(n_expand):
            new_node.x += self.path_resolution * math.cos(theta)
            new_node.y += self.path_resolution * math.sin(theta)
            new_node.path_x.append(new_node.x)
            new_node.path_y.append(new_node.y)

        d, _ = self._calc_distance_and_angle(new_node, to_node)
        if d <= self.path_resolution:
            new_node.path_x.append(to_node.x)
            new_node.path_y.append(to_node.y)
            new_node.x = to_node.x
            new_node.y = to_node.y

        new_node.parent = from_node
        return new_node

    def _generate_final_course(self, goal_ind) -> List[List[float]]:
        path = [[self.end.x, self.end.y]]
        node = self.node_list[goal_ind]
        while node.parent is not None:
            path.append([node.x, node.y])
            node = node.parent
        path.append([node.x, node.y])
        path.reverse()  # start -> goal order
        return path

    def _search_best_goal_node(self) -> Optional[int]:
        dist_list = [self._calc_dist_to_goal(n.x, n.y) for n in self.node_list]
        goal_inds = [i for i, d in enumerate(dist_list) if d <= self.expand_dis]

        safe_goal_inds = []
        for gi in goal_inds:
            t_node = self._steer(self.node_list[gi], self.end)
            if self._check_collision(t_node):
                safe_goal_inds.append(gi)

        if not safe_goal_inds:
            return None
        min_cost = min(self.node_list[i].cost for i in safe_goal_inds)
        for i in safe_goal_inds:
            if self.node_list[i].cost == min_cost:
                return i
        return None

    def _find_near_nodes(self, new_node) -> List[int]:
        nnode = len(self.node_list) + 1
        r = self.connect_circle_dist * math.sqrt(math.log(nnode) / nnode)
        r = min(r, self.expand_dis)
        dist_list = [(n.x - new_node.x) ** 2 + (n.y - new_node.y) ** 2
                     for n in self.node_list]
        return [i for i, d in enumerate(dist_list) if d <= r ** 2]

    def _choose_parent(self, new_node, near_inds):
        if not near_inds:
            return None
        costs = []
        for i in near_inds:
            near_node = self.node_list[i]
            t_node = self._steer(near_node, new_node)
            if t_node and self._check_collision(t_node):
                costs.append(self._calc_new_cost(near_node, new_node))
            else:
                costs.append(float("inf"))
        min_cost = min(costs)
        if min_cost == float("inf"):
            return None
        min_ind = near_inds[costs.index(min_cost)]
        chosen = self._steer(self.node_list[min_ind], new_node)
        chosen.cost = min_cost
        return chosen

    def _rewire(self, new_node, near_inds):
        for i in near_inds:
            near_node = self.node_list[i]
            edge_node = self._steer(new_node, near_node)
            if not edge_node:
                continue
            edge_node.cost = self._calc_new_cost(new_node, near_node)
            if self._check_collision(edge_node) and near_node.cost > edge_node.cost:
                near_node.x = edge_node.x
                near_node.y = edge_node.y
                near_node.cost = edge_node.cost
                near_node.path_x = edge_node.path_x
                near_node.path_y = edge_node.path_y
                near_node.parent = edge_node.parent
                self._propagate_cost_to_leaves(new_node)

    def _propagate_cost_to_leaves(self, parent_node):
        for node in self.node_list:
            if node.parent == parent_node:
                node.cost = self._calc_new_cost(parent_node, node)
                self._propagate_cost_to_leaves(node)

    def _calc_new_cost(self, from_node, to_node):
        d, _ = self._calc_distance_and_angle(from_node, to_node)
        return from_node.cost + d

    def _calc_dist_to_goal(self, x, y):
        return math.hypot(x - self.end.x, y - self.end.y)

    def _check_collision(self, node) -> bool:
        """True if the node's path is collision-free against the grid."""
        if node is None:
            return False
        for x, y in zip(node.path_x, node.path_y):
            if self.grid.is_occupied_world(x, y):
                return False
        return True

    @staticmethod
    def _calc_distance_and_angle(from_node, to_node):
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        return math.hypot(dx, dy), math.atan2(dy, dx)

    @staticmethod
    def _get_nearest_node_index(node_list, rnd_node):
        dlist = [(n.x - rnd_node.x) ** 2 + (n.y - rnd_node.y) ** 2 for n in node_list]
        return dlist.index(min(dlist))
