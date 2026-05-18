# Level 1 RTK Positioning Simulation Implementation Plan

## 1. Purpose

This document defines the Level 1 implementation plan for the RTK positioning module in the UAV Emergency Rescue System Based on BeiDou Navigation and Short Message Communication.

The RTK positioning module is located at:

```text
ros2_ws/src/rtk_positioning/
```

Level 1 is a standalone ROS 2 RTK positioning simulation. It demonstrates the effect of RTK correction by comparing raw GNSS positioning with RTK-corrected positioning.

Level 1 does not use PX4, Gazebo, QGroundControl, MAVLink `GPS_RTCM_DATA`, real RTCM data, real RTK hardware, real BeiDou satellite signal processing, or physical antenna modeling.

---

## 2. Level 1 Objective

The objective is to simulate:

```text
A moving UAV as the RTK rover
A fixed base station as the correction reference
Raw GNSS position with larger error
RTK-corrected position with smaller error
RTK status transitions
CSV logging for analysis
```

The expected result is:

```text
Raw GNSS error > RTK-corrected error
```

This is a software behavior model of RTK positioning, not a real RTK receiver implementation.

---

## 3. Level 1 Scope

### Included

```text
Simulated UAV movement
Fixed base station coordinate
Raw GNSS noise model
RTK correction model
RTK status model
Corrected RTK position output
Accuracy/error comparison
CSV logging
Standalone ROS 2 launch file
Basic documentation
```

### Not Included

```text
PX4/Gazebo UAV pose input
QGroundControl integration
MAVLink GPS_RTCM_DATA injection
Real RTCM decoding
Real RTK receiver firmware
Real BeiDou satellite RF simulation
Physical antenna simulation
Carrier-phase ambiguity resolution
```

---

## 4. Repository Rules

Use the existing repo structure.

RTK implementation location:

```text
ros2_ws/src/rtk_positioning/
```

Generated Level 1 logs:

```text
results/logs/rtk_positioning/level1/
```

Generated Level 1 graphs:

```text
results/graphs/rtk_positioning/level1/
```

Do not create a new RTK package outside `ros2_ws/src/rtk_positioning/`.

Do not modify other student modules:

```text
ros2_ws/src/qgc_control/
ros2_ws/src/target_detection_tracking/
ros2_ws/src/path_planning/
ros2_ws/src/beidou_short_message/
```

---

## 5. Level 1 Architecture

```text
Simulated UAV Node
        ↓
/uav/ground_truth

Base Station Node
        ↓
/rtk/base_station

RTK Positioning Node
        ↓
/uav/raw_gps
/uav/rtk_position
/uav/rtk_status
/rtk/accuracy
/rtk/error_metrics

Logger Node
        ↓
results/logs/rtk_positioning/level1/
```

The simulation uses three position concepts:

```text
Ground truth position:
The true simulated UAV position.

Raw GNSS position:
Ground truth plus normal GNSS noise.

RTK-corrected position:
Ground truth plus smaller RTK-level noise.
```

---

## 6. Expected Level 1 Folder Structure

```text
ros2_ws/src/rtk_positioning/
├── README.md
├── package.xml
├── setup.py
├── setup.cfg
│
├── src/
│   └── rtk_positioning/
│       ├── __init__.py
│       ├── base_station_node.py
│       ├── simulated_uav_node.py
│       ├── rtk_positioning_node.py
│       ├── gnss_noise_model.py
│       ├── rtk_correction_model.py
│       ├── coordinate_transform.py
│       ├── rtk_status_manager.py
│       └── logger_node.py
│
├── msg/
│   ├── RtkStatus.msg
│   └── RtkAccuracy.msg
│
├── config/
│   ├── level1_rtk_params.yaml
│   ├── base_station.yaml
│   └── noise_profiles.yaml
│
├── launch/
│   └── level1_rtk_sim.launch.py
│
└── docs/
    ├── LEVEL1_IMPLEMENTATION_PLAN.md
    ├── CLAUDE_LEVEL1_PROMPT.md
    ├── level1_conceptual_rtk_simulation.md
    ├── rtk_topic_interface.md
    └── simulation_assumptions.md
```

Generated outputs should be saved outside the ROS 2 package source folder:

```text
results/
├── logs/
│   └── rtk_positioning/
│       └── level1/
└── graphs/
    └── rtk_positioning/
        └── level1/
```

---

## 7. ROS 2 Topics

### Input Topics

| Topic | Message Type | Publisher | Subscriber | Purpose |
|---|---|---|---|---|
| `/uav/ground_truth` | `nav_msgs/msg/Odometry` | `simulated_uav_node` | `rtk_positioning_node`, `logger_node` | True simulated UAV position |
| `/rtk/base_station` | `sensor_msgs/msg/NavSatFix` | `base_station_node` | `rtk_positioning_node` | Fixed base station coordinate |

### Output Topics

| Topic | Message Type | Publisher | Purpose |
|---|---|---|---|
| `/uav/raw_gps` | `sensor_msgs/msg/NavSatFix` | `rtk_positioning_node` | Simulated noisy GNSS position |
| `/uav/rtk_position` | `sensor_msgs/msg/NavSatFix` | `rtk_positioning_node` | Simulated RTK-corrected position |
| `/uav/rtk_status` | `RtkStatus.msg` or temporary standard message | `rtk_positioning_node` | RTK state and correction quality |
| `/rtk/accuracy` | `RtkAccuracy.msg` or temporary standard message | `rtk_positioning_node` | Error and improvement metrics |
| `/rtk/error_metrics` | Standard message or CSV only | `rtk_positioning_node` or `logger_node` | Error analysis data |

If custom messages create build complexity, standard ROS 2 messages such as `std_msgs/msg/String` or `std_msgs/msg/Float32MultiArray` may be used temporarily, but this must be documented as a Level 1 simplification.

---

## 8. Nodes

### 8.1 `base_station_node.py`

Purpose: publish the fixed RTK base station coordinate.

Output:

```text
/rtk/base_station
```

Message type:

```text
sensor_msgs/msg/NavSatFix
```

Responsibilities:

```text
Load base station latitude, longitude, altitude, and frame_id from config/base_station.yaml.
Publish the fixed coordinate at 1 Hz.
Use frame_id = "base_station".
Keep the base station stationary.
```

---

### 8.2 `simulated_uav_node.py`

Purpose: simulate UAV movement without PX4 or Gazebo.

Output:

```text
/uav/ground_truth
```

Message type:

```text
nav_msgs/msg/Odometry
```

Responsibilities:

```text
Generate a repeatable UAV movement path.
Publish ground-truth UAV position.
Use a configurable publish rate.
Use a simple square-search path.
```

Recommended path:

```text
Start near base station
Move east
Move north
Move west
Move south
Return near start point
Repeat
```

---

### 8.3 `rtk_positioning_node.py`

Purpose: main Level 1 RTK simulation node.

Subscribed topics:

```text
/uav/ground_truth
/rtk/base_station
```

Published topics:

```text
/uav/raw_gps
/uav/rtk_position
/uav/rtk_status
/rtk/accuracy
/rtk/error_metrics
```

Responsibilities:

```text
Receive simulated UAV ground truth.
Convert local position into latitude, longitude, and altitude.
Generate raw GNSS position using larger simulated noise.
Generate RTK-corrected position using smaller simulated noise.
Publish raw GNSS position.
Publish RTK-corrected position.
Publish RTK status.
Publish accuracy/error data.
```

Important: this node must not claim to process real RTCM or real carrier-phase RTK measurements.

---

### 8.4 `logger_node.py`

Purpose: save Level 1 simulation outputs for analysis.

Output folder:

```text
results/logs/rtk_positioning/level1/
```

Responsibilities:

```text
Subscribe to ground truth, raw GNSS, RTK position, and RTK status topics.
Record timestamped data.
Save CSV logs.
Avoid overwriting previous logs.
Create output directory if missing.
```

Suggested CSV columns:

```text
timestamp
ground_truth_x
ground_truth_y
ground_truth_z
raw_gnss_latitude
raw_gnss_longitude
raw_gnss_altitude
rtk_latitude
rtk_longitude
rtk_altitude
raw_gnss_error_m
rtk_error_m
rtk_status
horizontal_accuracy_m
vertical_accuracy_m
```

---

## 9. Core Logic Files

### 9.1 `gnss_noise_model.py`

Purpose: provide reusable GNSS noise simulation functions.

Required modes:

```text
NORMAL_GNSS
RTK_FLOAT
RTK_FIXED
CORRECTION_LOST
```

Recommended values:

```text
normal_gnss_std_m: 1.5
rtk_float_std_m: 0.25
rtk_fixed_std_m: 0.03
correction_lost_std_m: 2.5
```

---

### 9.2 `rtk_correction_model.py`

Purpose: apply simulated RTK correction behavior.

Behavior:

```text
GNSS_ONLY: larger GNSS noise
RTK_FLOAT: medium-low RTK noise
RTK_FIXED: very small RTK noise
CORRECTION_LOST: degraded noise
```

This is not real RTCM processing.

---

### 9.3 `coordinate_transform.py`

Purpose: convert local simulation coordinates into approximate WGS84 coordinates.

Input:

```text
base latitude
base longitude
base altitude
local x offset in meters
local y offset in meters
local z offset in meters
```

Output:

```text
latitude
longitude
altitude
```

A simple local tangent plane approximation is acceptable for Level 1.

---

### 9.4 `rtk_status_manager.py`

Purpose: control simulated RTK state transitions.

Status codes:

```text
0 = NO_FIX
1 = GNSS_ONLY
2 = RTK_FLOAT
3 = RTK_FIXED
4 = CORRECTION_LOST
```

Level 1 transition pattern:

```text
0–5 seconds: GNSS_ONLY
5–15 seconds: RTK_FLOAT
15+ seconds: RTK_FIXED
```

---

## 10. Custom Messages

### 10.1 `RtkStatus.msg`

Suggested content:

```text
std_msgs/Header header
uint8 status_code
string status_text
bool correction_available
float32 correction_age_sec
float32 correction_quality
float32 horizontal_accuracy_m
float32 vertical_accuracy_m
```

Status codes:

```text
0 = NO_FIX
1 = GNSS_ONLY
2 = RTK_FLOAT
3 = RTK_FIXED
4 = CORRECTION_LOST
```

---

### 10.2 `RtkAccuracy.msg`

Suggested content:

```text
std_msgs/Header header
float32 raw_gnss_error_m
float32 rtk_error_m
float32 horizontal_accuracy_m
float32 vertical_accuracy_m
float32 improvement_percent
```

---

## 11. Configuration Files

### 11.1 `base_station.yaml`

```yaml
base_station:
  latitude: 39.981000
  longitude: 116.344000
  altitude: 50.0
  frame_id: "base_station"
```

### 11.2 `noise_profiles.yaml`

```yaml
noise:
  normal_gnss_std_m: 1.5
  rtk_float_std_m: 0.25
  rtk_fixed_std_m: 0.03
  correction_lost_std_m: 2.5
```

### 11.3 `level1_rtk_params.yaml`

```yaml
level1:
  publish_rate_hz: 10.0
  simulated_path: "square_search"
  default_status: "GNSS_ONLY"
  enable_csv_logging: true
  log_directory: "results/logs/rtk_positioning/level1"
```

---

## 12. Launch File

Create:

```text
ros2_ws/src/rtk_positioning/launch/level1_rtk_sim.launch.py
```

The launch file should start:

```text
base_station_node
simulated_uav_node
rtk_positioning_node
logger_node
```

Expected command:

```bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

---

## 13. Build and Run Commands

From repository root:

```bash
cd ros2_ws
colcon build --packages-select rtk_positioning
source install/setup.bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

Check topics:

```bash
ros2 topic list
```

Expected topics:

```text
/rtk/base_station
/uav/ground_truth
/uav/raw_gps
/uav/rtk_position
/uav/rtk_status
/rtk/accuracy
/rtk/error_metrics
```

Echo key topics:

```bash
ros2 topic echo /uav/raw_gps --once
ros2 topic echo /uav/rtk_position --once
ros2 topic echo /uav/rtk_status --once
```

Check logs:

```bash
ls ../results/logs/rtk_positioning/level1/
```

---

## 14. Expected Results

Level 1 should show:

```text
Raw GNSS error is larger.
RTK-corrected error is smaller.
RTK status transitions from GNSS_ONLY to RTK_FLOAT to RTK_FIXED.
CSV logs are generated.
The module publishes stable ROS 2 topics for future team integration.
```

Expected simulated error ranges:

```text
GNSS_ONLY: approximately 1–3 meters
RTK_FLOAT: approximately 0.2–0.5 meters
RTK_FIXED: approximately 0.02–0.05 meters
```

These are simulated values, not real hardware measurements.

---

## 15. Completion Criteria

Level 1 is complete when:

```text
The rtk_positioning package builds successfully.
The Level 1 launch file runs successfully.
The base station topic publishes fixed coordinates.
The simulated UAV ground-truth topic publishes movement.
The raw GNSS topic publishes noisy position.
The RTK position topic publishes corrected position.
The RTK status topic publishes GNSS_ONLY, RTK_FLOAT, and RTK_FIXED states.
The logger saves CSV output.
The output shows RTK error is smaller than raw GNSS error.
```

---

## 16. Future Level 2 Notes

Level 2 must reuse Level 1 logic.

Do not delete or break Level 1 when adding Level 2.

Level 2 will add:

```text
PX4/Gazebo pose adapter
Simulated GPS_RTCM_DATA-style correction behavior
Correction quality
Correction delay
Correction loss
Level 2 launch file
Level 2 logging
```

Level 1 must remain runnable at all times.
