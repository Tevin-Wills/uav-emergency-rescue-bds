# Claude Code Prompt: Level 1 RTK Positioning Simulation

Copy and paste this prompt into Claude Code while working inside the WSL terminal.

---

## Prompt

You are working inside an existing GitHub repository for a team UAV emergency rescue simulation project.

## Repository Context

Repository name:

```text
uav-emergency-rescue-bds
```

Main RTK module location:

```text
ros2_ws/src/rtk_positioning/
```

This module belongs to Student 1:

```text
RTK GNSS positioning
```

Expected RTK topics include:

```text
/uav/raw_gps
/uav/rtk_position
/uav/rtk_status
```

Shared output folders exist under:

```text
results/
```

Generated RTK Level 1 logs must go to:

```text
results/logs/rtk_positioning/level1/
```

Generated RTK Level 1 graphs must go to:

```text
results/graphs/rtk_positioning/level1/
```

## System Setup

The machine already has these installed and working:

```text
Ubuntu 24.04 in WSL
ROS 2 Jazzy
Gazebo Harmonic
PX4 SITL
QGroundControl
MAVLink
```

Do not repeat installation work.

---

## Current Task

Implement Level 1 only for the RTK positioning module.

Level 1 is a standalone conceptual RTK simulation.

It does not use:

```text
PX4
Gazebo
QGroundControl
MAVLink GPS_RTCM_DATA
real RTCM
real RTK hardware
real GNSS satellite signal processing
```

Level 1 should simulate:

```text
A moving UAV as the rover
A fixed base station coordinate
Raw GNSS position with larger noise
RTK-corrected position with smaller noise
RTK status transitions
Accuracy/error comparison
CSV logging for later analysis
```

Do not implement Level 2 in this prompt.

---

## Required Work Style

You must work in phases.

Do not do everything at once.

After each phase:

```text
1. Stop.
2. Summarize what you inspected or changed.
3. List changed files.
4. Provide verification commands.
5. Ask for approval before continuing to the next phase.
```

---

## Global Safety Rules

Follow these rules throughout the work:

```text
Inspect the repository structure before editing.
Read existing files before modifying them.
Do not overwrite existing files blindly.
Do not modify other student folders.
Do not modify project-level documentation unless necessary.
Keep Level 1 code inside ros2_ws/src/rtk_positioning/.
Save generated logs under results/logs/rtk_positioning/level1/.
Save generated plots under results/graphs/rtk_positioning/level1/.
Keep Level 1 runnable even when Level 2 is added later.
Make small, traceable changes.
Prefer simple, reliable ROS 2 Python code.
```

Do not modify these folders:

```text
ros2_ws/src/qgc_control/
ros2_ws/src/target_detection_tracking/
ros2_ws/src/path_planning/
ros2_ws/src/beidou_short_message/
```

---

# PHASE 0 — Repository Inspection Only

Do not edit any files in this phase.

Inspect:

```text
Current repo root
ros2_ws/src/rtk_positioning/
Existing package.xml
Existing setup.py
Existing setup.cfg
Existing README.md
Existing src/
Existing launch/
Existing config/
Existing msg/
Existing docs/
Existing results/logs/
Existing results/graphs/
Existing .gitignore
```

Report:

```text
Whether rtk_positioning is already a valid ROS 2 Python package
Which expected files are missing
Which files exist and should be preserved
Whether results/logs/rtk_positioning/level1 exists
Whether results/graphs/rtk_positioning/level1 exists
Recommended Phase 1 actions
```

Stop after Phase 0 and wait for approval.

---

# PHASE 1 — Package Skeleton and Safe Folder Preparation

Only proceed after approval.

Goal:

Make sure the RTK package has the required Level 1 folders and package skeleton.

Create missing folders only if needed:

```text
ros2_ws/src/rtk_positioning/src/rtk_positioning/
ros2_ws/src/rtk_positioning/launch/
ros2_ws/src/rtk_positioning/config/
ros2_ws/src/rtk_positioning/msg/
ros2_ws/src/rtk_positioning/docs/
results/logs/rtk_positioning/level1/
results/graphs/rtk_positioning/level1/
```

Create or update only if safe:

```text
package.xml
setup.py
setup.cfg
src/rtk_positioning/__init__.py
```

Required dependencies:

```text
rclpy
std_msgs
sensor_msgs
nav_msgs
geometry_msgs
builtin_interfaces
```

Important note about custom messages:

If custom messages create build complexity inside this Python package, explain the issue and recommend whether message definitions should move to the shared package:

```text
ros2_ws/src/interfaces/
```

Do not make risky message-generation changes without explaining them.

Stop after Phase 1 and wait for approval.

---

# PHASE 2 — Configuration Files

Only proceed after approval.

Create or update these files:

```text
ros2_ws/src/rtk_positioning/config/base_station.yaml
ros2_ws/src/rtk_positioning/config/noise_profiles.yaml
ros2_ws/src/rtk_positioning/config/level1_rtk_params.yaml
```

Use these starting values.

## `base_station.yaml`

```yaml
base_station:
  latitude: 39.981000
  longitude: 116.344000
  altitude: 50.0
  frame_id: "base_station"
```

## `noise_profiles.yaml`

```yaml
noise:
  normal_gnss_std_m: 1.5
  rtk_float_std_m: 0.25
  rtk_fixed_std_m: 0.03
  correction_lost_std_m: 2.5
```

## `level1_rtk_params.yaml`

```yaml
level1:
  publish_rate_hz: 10.0
  simulated_path: "square_search"
  default_status: "GNSS_ONLY"
  enable_csv_logging: true
  log_directory: "results/logs/rtk_positioning/level1"
```

Stop after Phase 2 and wait for approval.

---

# PHASE 3 — Core RTK Simulation Logic

Only proceed after approval.

Create these Python files:

```text
ros2_ws/src/rtk_positioning/src/rtk_positioning/gnss_noise_model.py
ros2_ws/src/rtk_positioning/src/rtk_positioning/rtk_correction_model.py
ros2_ws/src/rtk_positioning/src/rtk_positioning/coordinate_transform.py
ros2_ws/src/rtk_positioning/src/rtk_positioning/rtk_status_manager.py
```

## `gnss_noise_model.py`

Requirements:

```text
Provide functions/classes to apply Gaussian noise in meters.
Support normal GNSS, RTK float, RTK fixed, and correction lost noise modes.
Use deterministic optional random seed if configured.
Keep the code simple and testable.
```

## `rtk_correction_model.py`

Requirements:

```text
Provide a clean function/class that returns corrected position noise based on RTK status.
Do not claim to process real RTCM.
Use the noise values from configuration.
```

## `coordinate_transform.py`

Requirements:

```text
Convert local ENU-style x/y/z meter offsets into approximate WGS84 latitude/longitude/altitude.
Use base station latitude/longitude/altitude.
Keep the conversion simple and documented.
```

## `rtk_status_manager.py`

Requirements:

Support status codes:

```text
0 NO_FIX
1 GNSS_ONLY
2 RTK_FLOAT
3 RTK_FIXED
4 CORRECTION_LOST
```

For Level 1, implement this time-based transition:

```text
0–5 seconds: GNSS_ONLY
5–15 seconds: RTK_FLOAT
15+ seconds: RTK_FIXED
```

Add docstrings and comments explaining that this is a simulation model.

Stop after Phase 3 and wait for approval.

---

# PHASE 4 — ROS 2 Nodes

Only proceed after approval.

Create these nodes:

```text
ros2_ws/src/rtk_positioning/src/rtk_positioning/base_station_node.py
ros2_ws/src/rtk_positioning/src/rtk_positioning/simulated_uav_node.py
ros2_ws/src/rtk_positioning/src/rtk_positioning/rtk_positioning_node.py
ros2_ws/src/rtk_positioning/src/rtk_positioning/logger_node.py
```

## `base_station_node.py`

Requirements:

```text
Publish sensor_msgs/msg/NavSatFix on /rtk/base_station.
Load config/base_station.yaml if possible.
Publish at a low rate such as 1 Hz.
Use frame_id = "base_station".
```

## `simulated_uav_node.py`

Requirements:

```text
Publish nav_msgs/msg/Odometry on /uav/ground_truth.
Generate a repeatable square-search UAV movement path.
Publish at 10 Hz by default.
```

## `rtk_positioning_node.py`

Requirements:

```text
Subscribe to /uav/ground_truth.
Subscribe to /rtk/base_station or load base station config.
Publish sensor_msgs/msg/NavSatFix on /uav/raw_gps.
Publish sensor_msgs/msg/NavSatFix on /uav/rtk_position.
Publish RTK status on /uav/rtk_status.
Publish accuracy/error data on /rtk/accuracy if practical.
Use Level 1 status transitions.
Use raw GNSS noise for /uav/raw_gps.
Use RTK correction model for /uav/rtk_position.
```

## `logger_node.py`

Requirements:

```text
Subscribe to the Level 1 output topics.
Save CSV logs to results/logs/rtk_positioning/level1/.
Use timestamped file names to avoid overwriting.
Log ground truth, raw GNSS, RTK position, RTK status, and error metrics where available.
```

Important:

If custom messages are not fully configured yet, use standard messages temporarily:

```text
std_msgs/msg/String
std_msgs/msg/Float32MultiArray
```

Clearly document this as a Level 1 simplification.

Prefer robust build success over complex message setup.

Stop after Phase 4 and wait for approval.

---

# PHASE 5 — Launch File and Entry Points

Only proceed after approval.

Create:

```text
ros2_ws/src/rtk_positioning/launch/level1_rtk_sim.launch.py
```

Update `setup.py` entry points for:

```text
base_station_node
simulated_uav_node
rtk_positioning_node
logger_node
```

The launch file should start:

```text
base_station_node
simulated_uav_node
rtk_positioning_node
logger_node
```

Expected launch command:

```bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

Stop after Phase 5 and wait for approval.

---

# PHASE 6 — Documentation for Level 1

Only proceed after approval.

Create or update:

```text
ros2_ws/src/rtk_positioning/docs/LEVEL1_IMPLEMENTATION_PLAN.md
ros2_ws/src/rtk_positioning/docs/level1_conceptual_rtk_simulation.md
ros2_ws/src/rtk_positioning/docs/rtk_topic_interface.md
ros2_ws/src/rtk_positioning/docs/simulation_assumptions.md
```

Documentation must clearly state:

```text
Level 1 is not real RTK hardware.
Level 1 does not decode real RTCM.
Level 1 does not simulate BeiDou satellite RF signals.
Level 1 models RTK correction behavior using error reduction.
The UAV is treated as the rover.
The base station is a fixed coordinate.
Level 1 is designed to be extended into Level 2 later.
```

Stop after Phase 6 and wait for approval.

---

# PHASE 7 — Build and Verification

Only proceed after approval.

Run:

```bash
cd ros2_ws
colcon build --packages-select rtk_positioning
source install/setup.bash
```

Then run:

```bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

Verify:

```bash
ros2 topic list
ros2 topic echo /uav/raw_gps --once
ros2 topic echo /uav/rtk_position --once
ros2 topic echo /uav/rtk_status --once
ls ../results/logs/rtk_positioning/level1/ || true
```

If the build fails:

```text
Do not hide errors.
Explain the exact error.
Suggest the smallest fix.
Apply only after approval.
```

Stop after Phase 7 and wait for approval.

---

# PHASE 8 — Final Level 1 Summary

Only proceed after approval.

Provide:

```text
List of files created
List of files modified
Topics implemented
Launch command
Verification commands
Known limitations
What is ready for Level 2
What should not be claimed yet
```

Remember:

```text
Do not implement Level 2 in this prompt.
Do not modify other student modules.
Do not delete Level 1 files.
```
