# ROS 2 Topic Definitions

## Purpose

This file defines the shared ROS 2 topic names used across all five project modules. All team members must follow these topic names exactly to ensure modules integrate correctly.

---

## Topic Table

| Topic | Publisher | Subscriber(s) | Purpose | Message Type |
|---|---|---|---|---|
| `/uav/raw_gps` | `rtk_positioning` | `rtk_positioning` | Raw GNSS fix from receiver | `sensor_msgs/NavSatFix` |
| `/uav/rtk_position` | `rtk_positioning` | `path_planning`, `qgc_control` | RTK-corrected UAV position | `geometry_msgs/PoseStamped` |
| `/uav/rtk_status` | `rtk_positioning` | `qgc_control` | RTK fix quality (FLOAT/FIXED/NONE) | `std_msgs/String` |
| `/uav/telemetry` | `qgc_control` | All | UAV state and flight status | `std_msgs/String` (TBD) |
| `/rescue/beidou_message` | `beidou_short_message` | `qgc_control`, `path_planning` | Decoded BeiDou short message | Custom (see `message_formats.md`) |
| `/target/emergency_coordinate` | `beidou_short_message` | `qgc_control`, `path_planning` | Target rescue coordinate | Custom (see `coordinate_format.md`) |
| `/target/detection` | `target_detection_tracking` | `path_planning` | Whether target is detected | `std_msgs/Bool` |
| `/target/location` | `target_detection_tracking` | `path_planning` | Target pose estimate | `geometry_msgs/PoseStamped` |
| `/planner/path` | `path_planning` | `qgc_control` | Planned obstacle-free path | Custom (TBD) |
| `/mission/waypoints` | `qgc_control` | `path_planning` | QGC mission waypoints | Custom (TBD) |
| `/mission/status` | `qgc_control` | All | Current mission phase | `std_msgs/String` |
| `/camera/image_raw` | `target_detection_tracking` | `target_detection_tracking` | Raw camera feed | `sensor_msgs/Image` |
| `/map/obstacles` | `path_planning` | `path_planning` | Obstacle map | Custom (TBD) |

---

## Notes

- Topics marked TBD will be formalized in the `interfaces` ROS 2 package under `ros2_ws/src/interfaces/`.
- Custom message definitions must be agreed upon by the responsible module owner before implementation.
- Do not create new topics without updating this file first so all team members stay informed.

---

## PX4 Bridge Topics

PX4 publishes and subscribes to its own topics via the micro-XRCE-DDS bridge. Key PX4 topics used by this project:

| Topic | Direction | Purpose |
|---|---|---|
| `/fmu/out/vehicle_odometry` | PX4 → ROS 2 | Full vehicle odometry (used by rtk_positioning, path_planning) |
| `/fmu/in/trajectory_setpoint` | ROS 2 → PX4 | Path planning sends trajectory targets |
| `/fmu/in/vehicle_command` | ROS 2 → PX4 | Mission commands from qgc_control |
| `/fmu/out/vehicle_status` | PX4 → ROS 2 | Arm state, mode, health |
