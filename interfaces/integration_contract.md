# Integration Contract

## Purpose

This document defines what each module must provide as inputs and outputs to guarantee successful integration. Every team member must fulfil their contract before the final integration session.

---

## Module 1 — `rtk_positioning`

**Owner:** Student 1

**Inputs:**
- Raw GNSS data from receiver hardware or SITL simulation
- RTCM correction data from RTK base station

**Outputs:**
- `/uav/raw_gps` — raw GNSS fix (`sensor_msgs/NavSatFix`)
- `/uav/rtk_position` — RTK-corrected UAV position (`geometry_msgs/PoseStamped`)
- `/uav/rtk_status` — fix quality string: `RTK_FIXED`, `RTK_FLOAT`, or `NONE` (`std_msgs/String`)

**ROS 2 Topics Published:** `/uav/raw_gps`, `/uav/rtk_position`, `/uav/rtk_status`

**File Outputs:** RTK correction logs in `results/logs/`

**Expected Test Data:** Simulated GNSS fix with RTK correction, showing sub-5 cm horizontal error

**Integration Connection:** `path_planning` and `qgc_control` both subscribe to `/uav/rtk_position`

---

## Module 2 — `qgc_control`

**Owner:** Student 2

**Inputs:**
- `/target/emergency_coordinate` from `beidou_short_message`
- `/uav/rtk_position` from `rtk_positioning`
- MAVLink telemetry from PX4

**Outputs:**
- `/mission/waypoints` — QGC mission uploaded to PX4
- `/mission/status` — current mission phase
- `/uav/telemetry` — parsed UAV status

**ROS 2 Topics Published:** `/mission/waypoints`, `/mission/status`, `/uav/telemetry`

**File Outputs:** Mission `.plan` files in `missions/`

**Expected Test Data:** Successful waypoint upload and mission execution in PX4 SITL

**Integration Connection:** All modules subscribe to `/mission/status`; `path_planning` subscribes to `/mission/waypoints`

---

## Module 3 — `target_detection_tracking`

**Owner:** Student 3

**Inputs:**
- `/camera/image_raw` — camera feed from Gazebo simulation
- `/mission/status` — to activate detection at correct mission phase

**Outputs:**
- `/target/detection` — `true` when target is detected (`std_msgs/Bool`)
- `/target/location` — estimated target pose (`geometry_msgs/PoseStamped`)

**ROS 2 Topics Published:** `/target/detection`, `/target/location`

**File Outputs:** Detection screenshots in `results/screenshots/`

**Expected Test Data:** Successful detection and tracking of survivor marker model in Gazebo

**Integration Connection:** `path_planning` subscribes to `/target/location` for final landing guidance

---

## Module 4 — `path_planning`

**Owner:** Student 4

**Inputs:**
- `/uav/rtk_position` from `rtk_positioning`
- `/mission/waypoints` from `qgc_control`
- `/target/location` from `target_detection_tracking`
- `/map/obstacles` (internal, from obstacle detection)

**Outputs:**
- `/planner/path` — computed obstacle-free path
- `/fmu/in/trajectory_setpoint` — sent directly to PX4 bridge

**ROS 2 Topics Published:** `/planner/path`, `/fmu/in/trajectory_setpoint`

**File Outputs:** Path visualization graphs in `results/graphs/`

**Expected Test Data:** Successful obstacle-avoidance path from start to rescue target in Gazebo

**Integration Connection:** Receives data from all other modules; sends trajectory to PX4

---

## Module 5 — `beidou_short_message`

**Owner:** Student 5

**Inputs:**
- BeiDou hardware interface or software simulator
- Incoming short message with encoded rescue coordinates

**Outputs:**
- `/rescue/beidou_message` — raw decoded message (Custom)
- `/target/emergency_coordinate` — extracted rescue coordinate (Custom)

**ROS 2 Topics Published:** `/rescue/beidou_message`, `/target/emergency_coordinate`

**File Outputs:** Sample message logs in `data/sample_beidou_message.json`

**Expected Test Data:** Successfully decoded BeiDou short message with valid rescue coordinates

**Integration Connection:** `qgc_control` and `path_planning` subscribe to `/target/emergency_coordinate` to trigger mission planning

---

## Integration Readiness Checklist

Before the final integration session, each student must confirm:

- [ ] Module builds cleanly with `colcon build`
- [ ] Module runs without errors in isolation
- [ ] All required topics are published with correct names and types
- [ ] Test data is available in `data/` or `results/`
- [ ] `README.md` in the module package is up to date
- [ ] Individual report material is in `reports/student_X_*/`

---

## Final Integration Computer

The final integration will run on one main computer (native Ubuntu 24.04 recommended). All five modules will be launched together using `simulation/launch/full_rescue_sim.launch.py`.
