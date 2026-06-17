# ROS 2 Topic Definitions

## Purpose

This file defines the shared ROS 2 topic names used across the project modules. All team
members must follow these topic names and types exactly so modules integrate correctly.
This table reflects the **topics actually implemented in `ros2_ws/src/`** (verified against
the node source). The canonical module/topic wiring overview is in
[`../docs/PIPELINE_ARCHITECTURE.md`](../docs/PIPELINE_ARCHITECTURE.md).

---

## Application Topic Table

| Topic | Message Type | Publisher | Subscriber(s) | Purpose |
|---|---|---|---|---|
| `/uav/ground_truth` | `nav_msgs/Odometry` | `rtk_positioning` | `rtk_positioning` | Simulated ground-truth pose (error reference) |
| `/uav/raw_gps` | `sensor_msgs/NavSatFix` | `rtk_positioning` | `rtk_positioning` | Raw (uncorrected) GNSS fix |
| `/uav/rtk_position` | `sensor_msgs/NavSatFix` | `rtk_positioning` | `path_planning`, `target_detection_tracking` | RTK-corrected UAV position |
| `/uav/rtk_status` | `std_msgs/String` | `rtk_positioning` | `qgc_control`, `target_detection_tracking` | Fix quality `code\|name\|σ` (see message_formats.md) |
| `/uav/telemetry` | `std_msgs/String` | `qgc_control` (mission_status_node) | operators / dashboards | Aggregated phase + RTK quality |
| `/rtk/base_station` | `sensor_msgs/NavSatFix` | `rtk_positioning` | — | RTK base-station location |
| `/rtk/simulated_rtcm` | `interfaces/SimulatedRtcm` | `rtk_positioning` | `rtk_positioning` | Simulated RTCM correction stream |
| `/rtk/accuracy` | `std_msgs/Float32MultiArray` | `rtk_positioning` | `rtk_positioning` | Horizontal/vertical accuracy estimates |
| `/rtk/error_metrics` | `std_msgs/Float32MultiArray` | `rtk_positioning` | `rtk_positioning` | Position error vs ground truth |
| `/rtk/mission_viability` | `std_msgs/String` | `rtk_positioning` | `qgc_control` | Landing/approach viability gate |
| `/rtk/baseline_km` | `std_msgs/Float32` | `rtk_positioning` | — | Base↔rover baseline distance (km) |
| `/rescue/beidou_message` | `std_msgs/String` | `beidou_short_message` | monitor | Raw decoded BeiDou short message |
| `/target/emergency_coordinate` | `interfaces/EmergencyCoordinate` | `beidou_short_message` | `qgc_control`, `path_planning` | Extracted rescue coordinate |
| `/target/detection` | `std_msgs/Bool` | `target_detection_tracking` | `path_planning`, `qgc_control` | Whether a target is detected |
| `/target/location` | `geometry_msgs/PoseStamped` | `target_detection_tracking` | `path_planning` | Target pose estimate (`px4_local_enu`) |
| `/mission/status` | `std_msgs/String` | `qgc_control` (mission_status_node) | all modules | Current mission phase |
| `/mission/waypoints` | `nav_msgs/Path` | `qgc_control` (mission_status_node) | `path_planning` | Mission waypoints (latched) |
| `/planner/path` | `nav_msgs/Path` | `path_planning` | `qgc_control` | Planned obstacle-free path |
| `/map/obstacles` | `nav_msgs/OccupancyGrid` | `path_planning` | `path_planning` | Obstacle map (latched) |
| `/camera/image_raw` | `sensor_msgs/Image` | `ros_gz_bridge` (Gazebo) | `target_detection_tracking`, `qgc_control` | RGB camera feed |
| `/depth_camera` | `sensor_msgs/Image` | `ros_gz_bridge` (Gazebo) | `target_detection_tracking` | Depth camera feed |

> The mission state machine (`/mission/status`, `/mission/waypoints`, `/uav/telemetry`) runs
> as `mission_status_node` **inside the `qgc_control` package**, not a separate package.

---

## Notes

- Custom message definitions (`EmergencyCoordinate`, `SimulatedRtcm`) live in the `interfaces`
  ROS 2 package under `ros2_ws/src/interfaces/msg/`.
- Do not create new topics or change a type without updating this file first so all team
  members stay informed.
- `/camera/image_raw` and `/depth_camera` are bridged from Gazebo by `ros_gz_bridge`; the exact
  gz source topic depends on the sim model (see `docs/NATIVE_PC_RUNBOOK.md` §5).

---

## PX4 Bridge Topics

PX4 communicates over the micro-XRCE-DDS bridge using **instance namespacing** (`/px4_1/...`)
and **versioned** topic names (`..._v1`). Key topics used by this project:

| Topic | Direction | Purpose |
|---|---|---|
| `/px4_1/fmu/out/vehicle_local_position_v1` | PX4 → ROS 2 | Local position/velocity (used by target_detection, flight node) |
| `/px4_1/fmu/out/vehicle_status_v1` | PX4 → ROS 2 | Arm state, nav mode, health |
| `/px4_1/fmu/in/trajectory_setpoint` | ROS 2 → PX4 | Offboard trajectory targets (flight node) |
| `/px4_1/fmu/in/offboard_control_mode` | ROS 2 → PX4 | Offboard mode heartbeat |
| `/px4_1/fmu/in/vehicle_command` | ROS 2 → PX4 | Vehicle commands (arm, mode, etc.) |

> Namespace (`px4_ns`) and the `_v1` suffix must match the running PX4 build — confirm per
> `docs/NATIVE_PC_RUNBOOK.md` §5 on a new model.
