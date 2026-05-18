# Level 2 RTK Positioning Simulation Implementation Plan

## 1. Purpose of This Document

This document defines the Level 2 implementation plan for the RTK positioning module in the UAV Emergency Rescue System Based on BeiDou Navigation and Short Message Communication.

The RTK positioning module belongs to Student 1 and is located at:

```text
ros2_ws/src/rtk_positioning/
```

Level 2 builds on Level 1.

Level 1 proves the standalone RTK concept using a simulated UAV path, fixed base station, raw GNSS noise, RTK correction noise, RTK status, and logging.

Level 2 extends that work by connecting the RTK module more closely to the real team simulation stack:

```text
PX4 SITL
Gazebo Harmonic
ROS 2 Jazzy
QGroundControl
MAVLink-aware RTK behavior
```

Level 2 still does not use real RTK hardware.

Level 2 still does not decode real RTCM correction data.

Level 2 still does not simulate real BeiDou/GNSS RF satellite signals.

Instead, Level 2 adds a more realistic system-integration layer by using a PX4/Gazebo pose adapter and simulated GPS_RTCM_DATA-style correction behavior.

---

## 2. Level 2 Main Objective

The main objective of Level 2 is to extend the standalone Level 1 RTK simulation into a PX4/Gazebo-aware RTK positioning simulation.

Level 2 should demonstrate that:

```text
The UAV pose can come from the PX4/Gazebo simulation instead of only a fake standalone UAV path.
The RTK module can still publish raw GNSS, corrected RTK position, RTK status, and accuracy data.
The RTK correction behavior can depend on simulated correction-message quality, delay, and availability.
The RTK module remains compatible with future real RTK integration concepts.
```

The main upgrade is:

```text
Level 1:
simulated_uav_node → RTK positioning node

Level 2:
PX4/Gazebo vehicle pose → PX4 pose adapter → RTK positioning node
```

Level 2 should preserve Level 1.

Do not delete, break, or replace the Level 1 implementation.

---

## 3. Level 2 Scope

### 3.1 Included in Level 2

Level 2 includes:

```text
Reusing Level 1 RTK core logic
PX4/Gazebo pose adapter node
Simulated GPS_RTCM_DATA-style correction behavior
Simulated correction quality
Simulated correction delay
Simulated correction loss
RTK status transitions based on correction condition
Level 2 launch file
Level 2 configuration files
Level 2 CSV logging
Level 2 documentation
```

### 3.2 Not Included in Level 2

Level 2 does not include:

```text
Real RTK base station hardware
Real RTK rover receiver hardware
Real RTCM binary decoding
Real RTCM forwarding into PX4
Real MAVLink GPS_RTCM_DATA injection into a physical receiver
Real BeiDou/GNSS satellite RF signal simulation
Real carrier-phase ambiguity resolution
Physical GNSS antenna modeling
Claiming that PX4 SITL has achieved real RTK FIX from real RTCM
```

Level 2 is a MAVLink/PX4-aware simulation extension, not a real RTK hardware implementation.

---

## 4. Relationship Between Level 1 and Level 2

Level 2 must reuse Level 1.

The Level 1 work should remain runnable with:

```bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

Level 2 should add a new launch path:

```bash
ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py
```

The core RTK logic should remain shared.

The main difference is the data source.

### Level 1 Data Source

```text
simulated_uav_node.py
        ↓
/uav/ground_truth
        ↓
rtk_positioning_node.py
```

### Level 2 Data Source

```text
PX4/Gazebo vehicle pose
        ↓
px4_pose_adapter_node.py
        ↓
/uav/ground_truth
        ↓
rtk_positioning_node.py
```

The topic `/uav/ground_truth` should remain the normalized input to the RTK positioning node.

This allows Level 1 and Level 2 to share the same RTK logic.

---

## 5. GPS_RTCM_DATA-Style Behavior in Level 2

In real PX4 RTK workflows, the base station sends RTCM correction data through a ground-control pathway, commonly through QGroundControl and MAVLink.

The MAVLink message normally used to transport RTK correction data is known as:

```text
GPS_RTCM_DATA
```

In a real system:

```text
Physical RTK base station
        ↓
RTCM correction data
        ↓
QGroundControl / MAVLink
        ↓
GPS_RTCM_DATA message
        ↓
PX4 / UAV rover receiver
        ↓
RTK solution
```

For this simulation, Level 2 should not inject fake RTCM into PX4 and pretend real RTK is happening.

Instead, Level 2 should implement simulated GPS_RTCM_DATA-style behavior in ROS 2.

That means Level 2 should simulate:

```text
Correction message available
Correction message delayed
Correction message lost
Correction quality high or low
Correction age
Correction sequence ID
RTK status changes based on correction quality
```

This provides a realistic correction-transport model without falsely claiming real RTCM decoding.

---

## 6. Level 2 System Architecture

The Level 2 architecture is:

```text
PX4 SITL + Gazebo Harmonic
        ↓
PX4/Gazebo pose topic
        ↓
px4_pose_adapter_node.py
        ↓
/uav/ground_truth
        ↓
rtk_positioning_node.py
        ↓
/uav/raw_gps
/uav/rtk_position
/uav/rtk_status
/rtk/accuracy

base_station_node.py
        ↓
/rtk/base_station

rtcm_correction_simulator_node.py
        ↓
/rtk/simulated_rtcm
        ↓
rtk_positioning_node.py

logger_node.py
        ↓
results/logs/rtk_positioning/level2/
```

---

## 7. Required Repository Locations

All Level 2 source code must stay inside:

```text
ros2_ws/src/rtk_positioning/
```

Generated Level 2 logs must be saved under:

```text
results/logs/rtk_positioning/level2/
```

Generated Level 2 graphs must be saved under:

```text
results/graphs/rtk_positioning/level2/
```

Do not save generated logs inside the Python source folder.

Do not modify other student module folders unless explicitly approved.

---

## 8. Expected Final Level 2 Folder Additions

Level 2 should add or update the following files.

```text
ros2_ws/src/rtk_positioning/
├── src/
│   └── rtk_positioning/
│       ├── rtcm_correction_simulator_node.py
│       ├── px4_pose_adapter_node.py
│       └── rtk_positioning_node.py          # update carefully to support Level 2 mode
│
├── msg/
│   └── SimulatedRtcm.msg
│
├── config/
│   └── level2_rtk_params.yaml
│
├── launch/
│   └── level2_rtk_px4_sim.launch.py
│
└── docs/
    ├── LEVEL2_IMPLEMENTATION_PLAN.md
    ├── CLAUDE_LEVEL2_PROMPT.md
    ├── level2_mavlink_aware_rtk_simulation.md
    └── level2_px4_integration_notes.md
```

Generated outputs should be placed here:

```text
results/
├── logs/
│   └── rtk_positioning/
│       └── level2/
└── graphs/
    └── rtk_positioning/
        └── level2/
```

---

## 9. Level 2 ROS 2 Topics

### 9.1 Input Topics

| Topic | Message Type | Publisher | Subscriber | Purpose |
|---|---|---|---|---|
| PX4/Gazebo pose topic | Depends on bridge setup | PX4/Gazebo/bridge | `px4_pose_adapter_node` | Source vehicle pose |
| `/rtk/base_station` | `sensor_msgs/msg/NavSatFix` | `base_station_node` | `rtk_positioning_node` | Fixed base station coordinate |
| `/rtk/simulated_rtcm` | `SimulatedRtcm.msg` or temporary standard message | `rtcm_correction_simulator_node` | `rtk_positioning_node` | Simulated correction-message behavior |

### 9.2 Normalized Internal Topic

| Topic | Message Type | Publisher | Subscriber | Purpose |
|---|---|---|---|---|
| `/uav/ground_truth` | `nav_msgs/msg/Odometry` | `px4_pose_adapter_node` | `rtk_positioning_node`, `logger_node` | Normalized UAV pose used by RTK module |

### 9.3 Output Topics

| Topic | Message Type | Publisher | Purpose |
|---|---|---|---|
| `/uav/raw_gps` | `sensor_msgs/msg/NavSatFix` | `rtk_positioning_node` | Simulated raw GNSS position |
| `/uav/rtk_position` | `sensor_msgs/msg/NavSatFix` | `rtk_positioning_node` | Simulated RTK-corrected position |
| `/uav/rtk_status` | `RtkStatus.msg` or temporary standard message | `rtk_positioning_node` | RTK state and correction condition |
| `/rtk/accuracy` | `RtkAccuracy.msg` or temporary standard message | `rtk_positioning_node` | Raw GNSS error, RTK error, improvement |
| `/rtk/error_metrics` | Standard message or CSV only | `rtk_positioning_node` or `logger_node` | Error analysis data |

---

## 10. Level 2 Nodes

## 10.1 `px4_pose_adapter_node.py`

### Purpose

Receives UAV pose from PX4/Gazebo-related topics and republishes it in the normalized RTK format:

```text
/uav/ground_truth
```

### Why This Node Is Needed

PX4/Gazebo topic names and message types may differ depending on the bridge setup.

The RTK positioning node should not depend directly on PX4-specific topic details.

The adapter protects the RTK module from integration changes.

### Responsibilities

```text
Inspect available PX4/Gazebo/ROS 2 pose topics.
Subscribe to the configured pose source.
Convert pose into nav_msgs/msg/Odometry if needed.
Publish normalized UAV pose on /uav/ground_truth.
Support configurable input topic name.
Support fallback or clear error logging if the PX4 pose topic is unavailable.
```

### Important Behavior

The adapter should not generate a fake path when in Level 2 mode unless explicitly configured as fallback.

If PX4 pose is unavailable, it should log a clear warning and explain which topic it expected.

---

## 10.2 `rtcm_correction_simulator_node.py`

### Purpose

Simulates GPS_RTCM_DATA-style RTK correction-message behavior.

It does not publish real RTCM bytes.

It publishes correction condition information used by the RTK positioning node.

### Suggested Output Topic

```text
/rtk/simulated_rtcm
```

### Responsibilities

```text
Publish simulated correction availability.
Publish correction quality.
Publish correction age.
Publish correction sequence ID.
Simulate stable correction periods.
Simulate degraded correction periods.
Simulate correction loss events.
Allow parameters to control quality, delay, and loss.
```

### Example Behavior

```text
0–5 seconds:
correction_available = false
correction_quality = 0.0

5–15 seconds:
correction_available = true
correction_quality = 0.5
RTK status should become RTK_FLOAT

15–45 seconds:
correction_available = true
correction_quality = 0.95
RTK status should become RTK_FIXED

45–50 seconds:
correction_available = false
correction_quality = 0.0
RTK status should become CORRECTION_LOST or GNSS_ONLY

50+ seconds:
correction_available = true
correction_quality = 0.95
RTK status should recover to RTK_FIXED
```

---

## 10.3 `rtk_positioning_node.py` Level 2 Updates

### Purpose

The Level 1 RTK positioning node should be updated carefully so it can support both Level 1 and Level 2.

### New Level 2 Input

```text
/rtk/simulated_rtcm
```

### Required Behavior

```text
If running in Level 1:
Use time-based status transitions.

If running in Level 2:
Use simulated correction message quality, age, and availability to determine RTK status.
```

### Suggested Status Logic

```text
If correction_available is false:
    status = CORRECTION_LOST or GNSS_ONLY
    use degraded or normal GNSS-level noise

If correction_available is true and correction_quality >= fixed threshold:
    status = RTK_FIXED
    use RTK fixed noise

If correction_available is true and correction_quality >= float threshold:
    status = RTK_FLOAT
    use RTK float noise

If correction_available is true but correction_quality is too low:
    status = GNSS_ONLY
    use normal GNSS noise
```

Suggested thresholds:

```text
float_quality_threshold: 0.4
fixed_quality_threshold: 0.8
correction_timeout_sec: 2.0
```

---

## 10.4 `logger_node.py` Level 2 Updates

### Purpose

The logger should support Level 2 output logs.

### Output Location

```text
results/logs/rtk_positioning/level2/
```

### Additional Level 2 Columns

```text
correction_available
correction_quality
correction_age_sec
correction_sequence_id
px4_pose_source
rtk_status
raw_gnss_error_m
rtk_error_m
```

The logger should not break Level 1.

It should select Level 1 or Level 2 log directory based on configuration.

---

## 11. Simulated RTK Correction Message

## 11.1 `SimulatedRtcm.msg`

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

### Field Meaning

| Field | Meaning |
|---|---|
| `sequence_id` | Simulated correction message sequence |
| `fragment_id` | Simulated fragment number |
| `fragmented` | Whether this simulated correction is treated as fragmented |
| `length` | Simulated correction payload length |
| `correction_available` | Whether correction is currently available |
| `correction_age_sec` | Age of correction data |
| `correction_quality` | Quality score from 0.0 to 1.0 |
| `correction_source` | Example: `simulated_base_station` |

This message is not real MAVLink.

This message is not real RTCM.

It only represents correction transport behavior for simulation.

---

## 12. Level 2 Configuration File

## 12.1 `level2_rtk_params.yaml`

Suggested content:

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

Important note:

The default PX4 pose topic may need to be adjusted after inspecting actual ROS 2 topics from the local PX4 bridge.

Claude Code must inspect available topics before assuming a final topic name.

---

## 13. Level 2 Launch File

## 13.1 `level2_rtk_px4_sim.launch.py`

The launch file should start:

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

PX4 SITL and Gazebo may be launched separately by the team.

This launch file should not assume it is responsible for launching the entire PX4/Gazebo environment unless explicitly designed that way.

The Level 2 launch file should focus on the RTK module side.

---

## 14. Expected Level 2 Run Sequence

### Terminal 1: Start PX4 SITL with Gazebo

Example command may depend on the project setup.

Common PX4-style example:

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500
```

Use the actual project command if the repo provides a script.

### Terminal 2: Start ROS 2 bridge if required

Use the team’s existing PX4/ROS 2 bridge workflow.

If the bridge is already started by PX4 or scripts, do not duplicate it.

### Terminal 3: Run Level 2 RTK module

From repo root:

```bash
cd ros2_ws
colcon build --packages-select rtk_positioning
source install/setup.bash
ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py
```

### Verification

```bash
ros2 topic list
ros2 topic echo /uav/ground_truth --once
ros2 topic echo /rtk/simulated_rtcm --once
ros2 topic echo /uav/rtk_position --once
ros2 topic echo /uav/rtk_status --once
```

Check logs:

```bash
ls ../results/logs/rtk_positioning/level2/
```

---

## 15. Expected Level 2 Results

Level 2 should show:

```text
UAV pose can be taken from PX4/Gazebo through the adapter.
The RTK module still publishes raw GNSS and RTK-corrected position.
RTK status changes based on simulated correction-message behavior.
Correction loss causes degraded positioning.
Correction recovery restores RTK_FLOAT or RTK_FIXED.
Level 1 remains runnable.
Level 2 logs are saved separately from Level 1 logs.
```

Expected status behavior:

```text
Correction unavailable:
GNSS_ONLY or CORRECTION_LOST

Correction available but weak:
RTK_FLOAT

Correction available and strong:
RTK_FIXED
```

---

## 16. Git and Safety Rules

Implementation must follow these rules:

```text
Inspect files before editing.
Do not overwrite existing files blindly.
Do not modify other student module folders.
Do not break Level 1.
Keep Level 2 code inside ros2_ws/src/rtk_positioning/.
Save generated Level 2 logs in results/logs/rtk_positioning/level2/.
Save generated Level 2 graphs in results/graphs/rtk_positioning/level2/.
Keep changes small and traceable.
Run build/test after meaningful changes.
Report all changed files after each phase.
```

Other student folders that must not be modified:

```text
ros2_ws/src/qgc_control/
ros2_ws/src/target_detection_tracking/
ros2_ws/src/path_planning/
ros2_ws/src/beidou_short_message/
```

---

## 17. Level 2 Completion Criteria

Level 2 is complete when:

```text
Level 1 still builds and runs.
The Level 2 launch file runs without breaking Level 1.
The PX4 pose adapter publishes /uav/ground_truth from PX4/Gazebo pose input.
The simulated RTCM correction node publishes /rtk/simulated_rtcm.
The RTK positioning node uses correction quality/availability to control RTK status.
The RTK position output reacts correctly to RTK_FIXED, RTK_FLOAT, GNSS_ONLY, and CORRECTION_LOST.
CSV logs are saved under results/logs/rtk_positioning/level2/.
The implementation clearly documents that simulated RTCM is not real RTCM.
```

---

## 18. What Can Be Claimed After Level 2

After Level 2, it is fair to claim:

```text
The RTK module was extended from standalone conceptual simulation to PX4/Gazebo-aware simulation.
The UAV pose can be adapted from the simulation stack into the RTK module.
The module simulates GPS_RTCM_DATA-style correction behavior through correction quality, delay, and availability.
The RTK status changes realistically based on simulated correction conditions.
The module is structured for future real RTK hardware integration.
```

Do not claim:

```text
Real RTCM data was decoded.
Real MAVLink GPS_RTCM_DATA was injected into PX4 and processed by a real receiver.
Real RTK hardware was simulated at RF/carrier-phase level.
Real BeiDou satellite signals were simulated.
Real centimeter-level accuracy was achieved in hardware.
```

---

## 19. Notes for Future Work Beyond Level 2

Future work may include:

```text
Real MAVLink GPS_RTCM_DATA injection experiment
Real RTK base station and rover receiver
QGroundControl RTK correction workflow
RTK receiver hardware integration
Comparison of simulated RTK and real RTK logs
BeiDou-compatible receiver testing
```

These are beyond Level 2.
