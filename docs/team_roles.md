# Team Roles

This document defines the five project objectives and the responsibilities, inputs, outputs, and integration connections for each team member.

---

## Objective 1 — UAV RTK Positioning

**Module:** `rtk_positioning`
**Package path:** `ros2_ws/src/rtk_positioning/`

**Main Responsibility:**
Configure a simulated RTK base-rover GNSS setup and integrate RTK corrections into PX4 to achieve centimetre-level UAV positioning accuracy throughout the full flight.

**Inputs:**
- Raw GNSS data from GNSS receiver (or SITL simulation)
- RTCM correction data from RTK base station

**Outputs:**
- `/uav/raw_gps` — raw GNSS fix
- `/uav/rtk_position` — RTK-corrected UAV position
- `/uav/rtk_status` — fix quality (`RTK_FIXED`, `RTK_FLOAT`, `NONE`)

**Connection to Full System:**
`path_planning` and `qgc_control` both subscribe to `/uav/rtk_position` for navigation and monitoring.

---

## Objective 2 — UAV Control Using QGroundControl

**Module:** `qgc_control`
**Package path:** `ros2_ws/src/qgc_control/`

**Main Responsibility:**
Upload waypoint missions via QGroundControl, manage MAVLink telemetry between the ground station and PX4, and coordinate command flow between the GCS, ROS 2, and PX4.

**Inputs:**
- `/target/emergency_coordinate` from `beidou_short_message`
- `/uav/rtk_position` from `rtk_positioning`
- MAVLink telemetry from PX4 SITL

**Outputs:**
- `/mission/waypoints` — uploaded mission waypoints
- `/mission/status` — current mission phase
- `/uav/telemetry` — parsed UAV status

**Connection to Full System:**
All modules subscribe to `/mission/status`. `path_planning` uses `/mission/waypoints` to determine the planned route.

---

## Objective 3 — UAV Target Detection, Tracking, Following, and Fixed-Point Landing

**Module:** `target_detection_tracking`
**Package path:** `ros2_ws/src/target_detection_tracking/`

**Main Responsibility:**
Use the onboard camera feed from Gazebo to detect the rescue target, track and follow it during flight, and guide PX4 to a precision fixed-point landing over the target.

**Inputs:**
- `/camera/image_raw` — camera feed from Gazebo
- `/mission/status` — activates detection at the correct mission phase

**Outputs:**
- `/target/detection` — `true` when target is detected
- `/target/location` — estimated target pose

**Connection to Full System:**
`path_planning` subscribes to `/target/location` for the final landing guidance phase.

---

## Objective 4 — UAV Path Planning and Obstacle Avoidance

**Module:** `path_planning`
**Package path:** `ros2_ws/src/path_planning/`

**Main Responsibility:**
Compute an obstacle-free autonomous flight path from the UAV's current position to the rescue target location. Dynamically update the path if new obstacles are detected during flight. Publish trajectory setpoints directly to PX4.

**Inputs:**
- `/uav/rtk_position` from `rtk_positioning`
- `/mission/waypoints` from `qgc_control`
- `/target/location` from `target_detection_tracking`

**Outputs:**
- `/planner/path` — planned obstacle-free path
- `/fmu/in/trajectory_setpoint` — trajectory setpoints sent to PX4

**Connection to Full System:**
Receives data from all other modules and translates it into PX4-executable trajectory commands.

---

## Objective 5 — BeiDou Short Message Communication

**Module:** `beidou_short_message`
**Package path:** `ros2_ws/src/beidou_short_message/`

**Main Responsibility:**
Interface with the BeiDou short message hardware or software simulator. Decode incoming short messages to extract rescue coordinates, and forward those coordinates to the rest of the system via ROS 2.

**Inputs:**
- BeiDou hardware interface or software message simulator

**Outputs:**
- `/rescue/beidou_message` — raw decoded message
- `/target/emergency_coordinate` — extracted rescue coordinate

**Connection to Full System:**
`qgc_control` and `path_planning` subscribe to `/target/emergency_coordinate` to trigger mission planning.

---

## Shared Packages

### `interfaces`

**Package path:** `ros2_ws/src/interfaces/`

Shared custom ROS 2 message (`.msg`) and service (`.srv`) definitions used by all five modules. Ensures type consistency across the team.

### `bringup`

**Package path:** `ros2_ws/src/bringup/`

Full-system launch files that start all five modules together for integration testing and the final demonstration.

---

## Integration and Report Material

Each student stores their individual report material in:

```
reports/student_X_<module_name>/
```

See [`docs/integration_plan.md`](integration_plan.md) for the full integration sequence.
