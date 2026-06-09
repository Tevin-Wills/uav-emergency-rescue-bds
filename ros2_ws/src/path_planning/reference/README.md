# path_planning — reference source (NOT built)

`px4_rrt_avoidance/` is the **original contributed obstacle-avoidance package**, kept
here for provenance and attribution only. It is **not part of the build** (a
`COLCON_IGNORE` marker stops colcon from touching it).

## Why it is not used directly

It is a **ROS 1 / catkin / MAVROS / Gazebo-Classic / octomap** package and cannot
build or run in this ROS 2 Jazzy + Gazebo Harmonic + uXRCE-DDS project:
17 nodes import `rospy` (0 use `rclpy`), it depends on `mavros_msgs`, `tf`,
`octomap_server`, and a Gazebo-Classic SITL launch.

## What we salvaged (Option A)

The RRT* algorithm + grid-collision logic from `nodes/local_planner.py` (itself
derived from Atsushi Sakai's PythonRobotics RRT*, MIT) were lifted into a clean,
ROS-agnostic module and wrapped in a fresh ROS 2 node:

- `../src/path_planning/rrt_star_planner.py` — the salvaged RRT* (grid passed in)
- `../src/path_planning/obstacle_map.py` — synthetic obstacle grid + geodetic helpers
- `../src/path_planning/path_planning_node.py` — the rclpy node publishing `/planner/path`

## Excluded from this reference

The original `include/` directory (~14 MB of Gazebo-Classic `.dae` meshes, the
`gazebo_models/`, and two demo GIFs) was **not vendored** — those assets are
Gazebo-Classic-only and unusable here. The `world/*.world` files are kept as a
layout reference for the synthetic obstacle map.

A full ROS 1 → ROS 2 port (msgs via rosidl, MAVROS → px4_msgs/uXRCE, worlds →
Gazebo Harmonic SDF) is possible later but was out of scope for the integration
deadline.
