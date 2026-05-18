# Claude Code Prompt: Level 2 RTK Positioning Simulation

Copy and paste the prompt below into Claude Code while working inside the WSL terminal.

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

Level 1 should already exist or be in progress.

Existing expected RTK topics include:

```text
/uav/raw_gps
/uav/rtk_position
/uav/rtk_status
```

Shared output folders already exist under:

```text
results/
```

Generated Level 2 RTK logs must go to:

```text
results/logs/rtk_positioning/level2/
```

Generated Level 2 RTK graphs must go to:

```text
results/graphs/rtk_positioning/level2/
```

## System Setup

The machine already has the following installed and working:

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

Implement Level 2 for the RTK positioning module.

Level 2 must build on Level 1.

Level 2 is a PX4/Gazebo-aware and MAVLink-aware RTK simulation extension.

Level 2 should add:

```text
PX4/Gazebo pose adapter
Simulated GPS_RTCM_DATA-style correction behavior
Correction quality
Correction delay
Correction loss
RTK status transitions based on correction conditions
Level 2 launch file
Level 2 configuration
Level 2 logging
```

Level 2 must not delete or break Level 1.

Level 1 should remain runnable with:

```bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

Level 2 should be runnable with:

```bash
ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py
```

---

## Important Technical Boundary

Level 2 does not use real RTK hardware.

Level 2 does not decode real RTCM.

Level 2 does not simulate real BeiDou/GNSS RF signals.

Level 2 does not need to inject real MAVLink GPS_RTCM_DATA into PX4.

Instead, Level 2 simulates GPS_RTCM_DATA-style behavior in ROS 2 by modeling:

```text
Correction availability
Correction quality
Correction age
Correction sequence ID
Correction delay
Correction loss
RTK_FIXED / RTK_FLOAT / GNSS_ONLY / CORRECTION_LOST transitions
```

Do not falsely claim real RTCM or real RTK receiver processing.

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
Keep Level 2 code inside ros2_ws/src/rtk_positioning/.
Save generated logs under results/logs/rtk_positioning/level2/.
Save generated plots under results/graphs/rtk_positioning/level2/.
Do not break Level 1.
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

# PHASE 0 — Level 1 and Repository Verification

Do not edit any files in this phase.

Inspect:

```text
Current repo root
ros2_ws/src/rtk_positioning/
Existing Level 1 files
Existing package.xml
Existing setup.py
Existing setup.cfg
Existing src/
Existing launch/
Existing config/
Existing msg/
Existing docs/
Existing results/logs/rtk_positioning/
Existing results/graphs/rtk_positioning/
Existing .gitignore
```

Verify whether these Level 1 files exist:

```text
level1_rtk_sim.launch.py
base_station_node.py
simulated_uav_node.py
rtk_positioning_node.py
gnss_noise_model.py
rtk_correction_model.py
coordinate_transform.py
rtk_status_manager.py
logger_node.py
```

Report:

```text
Whether Level 1 appears complete
Whether Level 1 build files exist
Whether Level 1 should be tested before Level 2
Which files must be preserved
Which Level 2 files are missing
Recommended Phase 1 actions
```

Stop after Phase 0 and wait for approval.

---

# PHASE 1 — Inspect PX4/Gazebo/ROS 2 Pose Topic Availability

Only proceed after approval.

Goal:

Determine how the RTK module can receive UAV pose from PX4/Gazebo.

Do not edit files in this phase unless needed to save notes.

Inspect available ROS 2 topics after the user starts PX4/Gazebo/bridge, or provide clear commands for the user to run:

```bash
ros2 topic list
ros2 topic info <candidate_topic>
ros2 interface show <message_type>
```

Candidate topics may include but are not limited to:

```text
/fmu/out/vehicle_odometry
/fmu/out/vehicle_local_position
/model/x500/odometry
/world/*/model/*/pose
```

Do not assume the final topic name without inspection.

Report:

```text
Which pose topics are available
Which topic is best for px4_pose_adapter_node.py
What message type it uses
Whether conversion to nav_msgs/msg/Odometry is needed
Recommended config value for px4_pose_topic
```

Stop after Phase 1 and wait for approval.

---

# PHASE 2 — Level 2 Folder and Config Preparation

Only proceed after approval.

Create missing folders only if needed:

```text
results/logs/rtk_positioning/level2/
results/graphs/rtk_positioning/level2/
```

Create or update:

```text
ros2_ws/src/rtk_positioning/config/level2_rtk_params.yaml
```

Use this starting structure, but update `px4_pose_topic` if Phase 1 found a better topic:

```yaml
level2:
  use_px4_pose: true
  px4_pose_topic: "/fmu/out/vehicle_odometry"
  normalized_pose_topic: "/uav/ground_truth"

  use_simulated_rtcm: true
  simulated_rtcm_topic: "/rtk/simulated_rtcm"

  correction_timeout_sec: 2.0
  float_quality_threshold: 0.4
  fixed_quality_threshold: 0.8

  publish_rate_hz: 10.0

  enable_csv_logging: true
  log_directory: "results/logs/rtk_positioning/level2"

rtcm_simulation:
  publish_rate_hz: 5.0
  correction_source: "simulated_base_station"
  stable_quality: 0.95
  float_quality: 0.5
  lost_quality: 0.0
  simulated_length_bytes: 120
```

Stop after Phase 2 and wait for approval.

---

# PHASE 3 — Simulated RTCM Message Interface

Only proceed after approval.

Goal:

Add or prepare a message/interface for simulated GPS_RTCM_DATA-style behavior.

Preferred file:

```text
ros2_ws/src/rtk_positioning/msg/SimulatedRtcm.msg
```

Suggested content:

```text
std_msgs/Header header
uint8 sequence_id
uint8 fragment_id
bool fragmented
uint16 length
bool correction_available
float32 correction_age_sec
float32 correction_quality
string correction_source
```

Important:

If adding a custom message to the Python package creates build complexity, explain the issue and propose one of these options:

```text
Option A: Configure rtk_positioning package to build custom messages correctly.
Option B: Move shared/custom messages to ros2_ws/src/interfaces/.
Option C: Temporarily use std_msgs/msg/String or std_msgs/msg/Float32MultiArray for Level 2.
```

Do not make risky message-generation changes without explaining them.

Stop after Phase 3 and wait for approval.

---

# PHASE 4 — RTCM Correction Simulator Node

Only proceed after approval.

Create:

```text
ros2_ws/src/rtk_positioning/src/rtk_positioning/rtcm_correction_simulator_node.py
```

Requirements:

```text
Publish simulated correction information on /rtk/simulated_rtcm.
Do not publish real RTCM bytes.
Do not claim real MAVLink GPS_RTCM_DATA injection.
Publish correction availability.
Publish correction quality.
Publish correction age.
Publish sequence ID.
Publish correction source.
Support configurable publish rate.
Support configurable quality profile.
```

Recommended simulation pattern:

```text
0–5 seconds:
correction_available = false
correction_quality = 0.0

5–15 seconds:
correction_available = true
correction_quality = 0.5

15–45 seconds:
correction_available = true
correction_quality = 0.95

45–50 seconds:
correction_available = false
correction_quality = 0.0

50+ seconds:
correction_available = true
correction_quality = 0.95
```

This should drive status behavior:

```text
No correction → GNSS_ONLY or CORRECTION_LOST
Medium correction → RTK_FLOAT
Strong correction → RTK_FIXED
```

Stop after Phase 4 and wait for approval.

---

# PHASE 5 — PX4 Pose Adapter Node

Only proceed after approval.

Create:

```text
ros2_ws/src/rtk_positioning/src/rtk_positioning/px4_pose_adapter_node.py
```

Purpose:

Convert PX4/Gazebo pose output into the normalized RTK topic:

```text
/uav/ground_truth
```

Requirements:

```text
Subscribe to the configured PX4/Gazebo pose topic.
Publish nav_msgs/msg/Odometry on /uav/ground_truth.
Support configurable input topic name from level2_rtk_params.yaml.
Log clear warnings if the PX4 pose topic is not available.
Do not generate fake movement unless fallback mode is explicitly enabled.
Keep the adapter isolated so rtk_positioning_node.py does not depend directly on PX4 topic details.
```

If the actual PX4 topic uses `px4_msgs/msg/VehicleOdometry`, convert the fields into `nav_msgs/msg/Odometry`.

If the actual topic already uses `nav_msgs/msg/Odometry`, republish or remap as needed.

If the message type is uncertain, document the uncertainty and implement the cleanest option based on Phase 1 findings.

Stop after Phase 5 and wait for approval.

---

# PHASE 6 — Update RTK Positioning Node for Level 2 Mode

Only proceed after approval.

Carefully update:

```text
ros2_ws/src/rtk_positioning/src/rtk_positioning/rtk_positioning_node.py
```

Do not break Level 1.

Requirements:

```text
Support Level 1 mode with time-based RTK status.
Support Level 2 mode with correction-message-based RTK status.
Subscribe to /rtk/simulated_rtcm in Level 2 mode.
Use correction_available, correction_quality, and correction_age_sec to determine RTK status.
Use thresholds from level2_rtk_params.yaml.
```

Suggested Level 2 status logic:

```text
If correction_available is false:
    status = CORRECTION_LOST or GNSS_ONLY
    use degraded or normal GNSS noise

If correction_available is true and correction_quality >= fixed_quality_threshold:
    status = RTK_FIXED
    use rtk_fixed_std_m

If correction_available is true and correction_quality >= float_quality_threshold:
    status = RTK_FLOAT
    use rtk_float_std_m

If correction_available is true but correction_quality is too low:
    status = GNSS_ONLY
    use normal_gnss_std_m
```

Correction timeout logic:

```text
If last correction message age exceeds correction_timeout_sec:
    status = CORRECTION_LOST
```

Stop after Phase 6 and wait for approval.

---

# PHASE 7 — Update Logger for Level 2

Only proceed after approval.

Carefully update:

```text
ros2_ws/src/rtk_positioning/src/rtk_positioning/logger_node.py
```

Do not break Level 1 logging.

Requirements:

```text
Support Level 1 log directory.
Support Level 2 log directory.
Log correction availability.
Log correction quality.
Log correction age.
Log correction sequence ID.
Log RTK status.
Log raw GNSS error.
Log RTK error.
```

Level 2 output directory:

```text
results/logs/rtk_positioning/level2/
```

Use timestamped filenames.

Stop after Phase 7 and wait for approval.

---

# PHASE 8 — Level 2 Launch File and Entry Points

Only proceed after approval.

Create:

```text
ros2_ws/src/rtk_positioning/launch/level2_rtk_px4_sim.launch.py
```

Update `setup.py` entry points for:

```text
rtcm_correction_simulator_node
px4_pose_adapter_node
```

Do not remove Level 1 entry points.

The Level 2 launch file should start:

```text
base_station_node
px4_pose_adapter_node
rtcm_correction_simulator_node
rtk_positioning_node
logger_node
```

Expected command:

```bash
ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py
```

Important:

Do not make this launch file responsible for the entire PX4/Gazebo environment unless the repository already has a reliable project script for that.

Assume PX4/Gazebo may be started separately.

Stop after Phase 8 and wait for approval.

---

# PHASE 9 — Documentation for Level 2

Only proceed after approval.

Create or update:

```text
ros2_ws/src/rtk_positioning/docs/LEVEL2_IMPLEMENTATION_PLAN.md
ros2_ws/src/rtk_positioning/docs/CLAUDE_LEVEL2_PROMPT.md
ros2_ws/src/rtk_positioning/docs/level2_mavlink_aware_rtk_simulation.md
ros2_ws/src/rtk_positioning/docs/level2_px4_integration_notes.md
```

Documentation must clearly state:

```text
Level 2 builds on Level 1.
Level 2 adds PX4/Gazebo pose input through an adapter.
Level 2 adds simulated GPS_RTCM_DATA-style correction behavior.
Level 2 does not decode real RTCM.
Level 2 does not inject real RTCM into PX4.
Level 2 does not simulate real BeiDou/GNSS RF signals.
Level 1 must remain runnable.
```

Stop after Phase 9 and wait for approval.

---

# PHASE 10 — Build and Verification

Only proceed after approval.

First verify Level 1 still builds:

```bash
cd ros2_ws
colcon build --packages-select rtk_positioning
source install/setup.bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

Then verify Level 2.

Start PX4/Gazebo separately using the team’s known working command.

Then run:

```bash
cd ros2_ws
source install/setup.bash
ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py
```

Verify:

```bash
ros2 topic list
ros2 topic echo /uav/ground_truth --once
ros2 topic echo /rtk/simulated_rtcm --once
ros2 topic echo /uav/raw_gps --once
ros2 topic echo /uav/rtk_position --once
ros2 topic echo /uav/rtk_status --once
ls ../results/logs/rtk_positioning/level2/ || true
```

If the build fails:

```text
Do not hide errors.
Explain the exact error.
Suggest the smallest fix.
Apply only after approval.
```

Stop after Phase 10 and wait for approval.

---

# PHASE 11 — Final Level 2 Summary

Only proceed after approval.

Provide:

```text
List of files created
List of files modified
Topics implemented
Launch command
Verification commands
Known limitations
What is ready for future real RTK hardware extension
What should not be claimed yet
Confirmation that Level 1 still works
```

Remember:

```text
Do not delete Level 1 files.
Do not modify other student modules.
Do not claim real RTCM or real RTK hardware processing.
```
