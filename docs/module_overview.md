# Module Overview

This document summarises each ROS2 package in the repository, its owner, scope, and key interfaces.

---

## Member 1 — `rtk_positioning`

**Responsibility:** High-precision RTK GNSS positioning for the UAV.

**Scope:**
- Configure RTK base station and rover hardware.
- Integrate RTCM correction data into PX4.
- Publish precise pose and status topics.

**Key ROS2 Topics:**

| Topic | Direction | Type |
|-------|-----------|------|
| `/uav/rtk_pose` | Publish | `geometry_msgs/PoseStamped` |
| `/uav/rtk_status` | Publish | `std_msgs/String` |

**Package path:** `ros2_ws/src/rtk_positioning/`

---

## Member 2 — `uav_control_gcs`

**Responsibility:** UAV control via QGroundControl and MAVLink telemetry management.

**Scope:**
- Mission upload and monitoring through QGroundControl.
- Telemetry parsing and forwarding.
- Command flow between GCS, ROS2, and PX4.

**Key ROS2 Topics:**

| Topic | Direction | Type |
|-------|-----------|------|
| `/uav/mission_waypoints` | Publish | TBD (interfaces) |
| `/uav/telemetry_status` | Publish | TBD |

**Package path:** `ros2_ws/src/uav_control_gcs/`

---

## Member 3 — `target_tracking_landing`

**Responsibility:** Camera-based target detection, tracking, following, and fixed-point landing.

**Scope:**
- Detect rescue target using onboard camera.
- Track and follow the target during flight.
- Guide PX4 to a fixed-point precision landing over the target.

**Key ROS2 Topics:**

| Topic | Direction | Type |
|-------|-----------|------|
| `/uav/target_pose` | Publish | `geometry_msgs/PoseStamped` |
| `/uav/target_detected` | Publish | `std_msgs/Bool` |

**Package path:** `ros2_ws/src/target_tracking_landing/`

---

## Member 4 — `path_planning_rescue`

**Responsibility:** Autonomous obstacle avoidance and mission route planning.

**Scope:**
- Plan obstacle-free routes to rescue coordinates.
- Dynamically update path in response to obstacle detection.
- Publish trajectory setpoints to PX4.

**Key ROS2 Topics:**

| Topic | Direction | Type |
|-------|-----------|------|
| `/px4/trajectory_setpoint` | Publish | `px4_msgs/TrajectorySetpoint` |
| `/uav/rtk_pose` | Subscribe | `geometry_msgs/PoseStamped` |
| `/uav/target_pose` | Subscribe | `geometry_msgs/PoseStamped` |

**Package path:** `ros2_ws/src/path_planning_rescue/`

---

## Member 5 — `beidou_sms`

**Responsibility:** BeiDou short message send/receive and rescue coordinate forwarding.

**Scope:**
- Interface with BeiDou SMS hardware or simulator.
- Decode incoming short messages to extract rescue coordinates.
- Forward coordinates to the rest of the system via ROS2.

**Key ROS2 Topics:**

| Topic | Direction | Type |
|-------|-----------|------|
| `/beidou/rescue_coords` | Publish | TBD (interfaces) |
| `/beidou/send_message` | Subscribe | TBD |

**Package path:** `ros2_ws/src/beidou_sms/`

---

## Shared — `interfaces`

**Responsibility:** Shared custom ROS2 message and service definitions used across all packages.

**Contents:**
- `msg/` — custom message types (e.g., rescue coordinates, mission state)
- `srv/` — custom service types (e.g., mission start/stop)

**Package path:** `ros2_ws/src/interfaces/`

---

## Shared — `bringup`

**Responsibility:** Full-system launch files for simulation and integration testing.

**Contents:**
- Launch files that start all modules together.
- System-level configuration.

**Package path:** `ros2_ws/src/bringup/`

---

## TODO

- [ ] Finalize all topic names and message types with the team
- [ ] Define service interfaces in `interfaces`
- [ ] Document inter-module dependencies
