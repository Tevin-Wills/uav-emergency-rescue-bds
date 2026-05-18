# RTK Positioning — Level 1 Topic Interface

## Overview

This document describes all ROS 2 topics published and subscribed by the Level 1 RTK positioning simulation.

Topics follow the shared interface contract defined in:

```
interfaces/ros2_topics.md
interfaces/coordinate_format.md
```

---

## Topic Summary Table

| Topic | Direction | Message Type | Rate | Publisher | Subscriber |
|---|---|---|---|---|---|
| `/rtk/base_station` | Output | `sensor_msgs/msg/NavSatFix` | 1 Hz | `base_station_node` | `rtk_positioning_node` |
| `/uav/ground_truth` | Internal | `nav_msgs/msg/Odometry` | 10 Hz | `simulated_uav_node` | `rtk_positioning_node`, `logger_node` |
| `/uav/raw_gps` | Output | `sensor_msgs/msg/NavSatFix` | 10 Hz | `rtk_positioning_node` | `logger_node` |
| `/uav/rtk_position` | Output | `sensor_msgs/msg/NavSatFix` | 10 Hz | `rtk_positioning_node` | `logger_node` |
| `/uav/rtk_status` | Output | `std_msgs/msg/String` (L1) | 10 Hz | `rtk_positioning_node` | `logger_node` |
| `/rtk/accuracy` | Output | `std_msgs/msg/Float32MultiArray` (L1) | 10 Hz | `rtk_positioning_node` | `logger_node` |

---

## Topic Details

### `/rtk/base_station`

**Type:** `sensor_msgs/msg/NavSatFix`

**Publisher:** `base_station_node`

**Purpose:** Fixed RTK base station coordinate. Updated at 1 Hz throughout the simulation. The `rtk_positioning_node` uses this to keep the base station coordinate current.

**Key fields:**

| Field | Value |
|---|---|
| `header.frame_id` | `"base_station"` |
| `status.status` | `STATUS_FIX` (0) |
| `latitude` | 39.981000° (configurable) |
| `longitude` | 116.344000° (configurable) |
| `altitude` | 50.0 m (configurable) |

---

### `/uav/ground_truth`

**Type:** `nav_msgs/msg/Odometry`

**Publisher:** `simulated_uav_node`

**Purpose:** True UAV position in ENU meters relative to the base station. Used by `rtk_positioning_node` to generate GNSS and RTK positions. Used by `logger_node` for error computation.

**Key fields:**

| Field | Value |
|---|---|
| `header.frame_id` | `"map"` |
| `child_frame_id` | `"uav_base_link"` |
| `pose.pose.position.x` | East offset (meters) |
| `pose.pose.position.y` | North offset (meters) |
| `pose.pose.position.z` | Altitude AGL (meters, default 30.0) |

---

### `/uav/raw_gps`

**Type:** `sensor_msgs/msg/NavSatFix`

**Publisher:** `rtk_positioning_node`

**Purpose:** Simulated raw GNSS position. Always uses GNSS_ONLY noise level (std ≈ 1.5 m) regardless of RTK status. Represents what a standalone GPS receiver would report.

**Key fields:**

| Field | Value |
|---|---|
| `header.frame_id` | `"gps"` |
| `status.status` | `STATUS_FIX` (0) |
| `position_covariance_type` | `COVARIANCE_TYPE_DIAGONAL_KNOWN` |
| `position_covariance[0,4,8]` | `std² = 2.25` (1.5² m²) |

---

### `/uav/rtk_position`

**Type:** `sensor_msgs/msg/NavSatFix`

**Publisher:** `rtk_positioning_node`

**Purpose:** Simulated RTK-corrected position. Noise level decreases as RTK status improves. This is the high-accuracy position output that other modules (path planning, target detection) should use.

**Key fields:**

| Field | Value |
|---|---|
| `header.frame_id` | `"gps"` |
| `status.status` | `STATUS_FIX` / `STATUS_SBAS_FIX` / `STATUS_GBAS_FIX` depending on RTK status |
| `position_covariance[0,4,8]` | Varies: 2.25 / 0.0625 / 0.0009 m² (GNSS/FLOAT/FIXED) |

---

### `/uav/rtk_status`

**Type:** `std_msgs/msg/String` *(Level 1 simplification)*

**Publisher:** `rtk_positioning_node`

**Purpose:** Current RTK fix state and accuracy. Custom message `RtkStatus.msg` is planned for Level 2 when the `interfaces` package is built out.

**Format:**

```
"<status_code>|<status_name>|<accuracy_m>"
```

**Examples:**

```
"1|GNSS_ONLY|1.5000"
"2|RTK_FLOAT|0.2500"
"3|RTK_FIXED|0.0300"
"4|CORRECTION_LOST|2.5000"
```

**Status codes:**

| Code | Name | Meaning |
|---|---|---|
| 0 | NO_FIX | No satellite fix |
| 1 | GNSS_ONLY | Standard GPS only |
| 2 | RTK_FLOAT | Correction active, float ambiguity |
| 3 | RTK_FIXED | Full RTK fix |
| 4 | CORRECTION_LOST | Previously had fix, now lost |

---

### `/rtk/accuracy`

**Type:** `std_msgs/msg/Float32MultiArray` *(Level 1 simplification)*

**Publisher:** `rtk_positioning_node`

**Purpose:** Accuracy comparison between raw GNSS and RTK-corrected position. Custom message `RtkAccuracy.msg` is planned for Level 2.

**Format:** `[raw_gnss_std_m, rtk_std_m, improvement_percent]`

**Examples:**

```
GNSS_ONLY:   [1.5, 1.5,   0.0]
RTK_FLOAT:   [1.5, 0.25, 83.3]
RTK_FIXED:   [1.5, 0.03, 98.0]
```

---

## Future Custom Messages

When the `interfaces` package is fully configured as an `ament_cmake` package, these custom messages will replace the Level 1 simplifications:

### `RtkStatus.msg`

```
std_msgs/Header header
uint8 status_code
string status_text
bool correction_available
float32 correction_age_sec
float32 correction_quality
float32 horizontal_accuracy_m
float32 vertical_accuracy_m
```

### `RtkAccuracy.msg`

```
std_msgs/Header header
float32 raw_gnss_error_m
float32 rtk_error_m
float32 horizontal_accuracy_m
float32 vertical_accuracy_m
float32 improvement_percent
```
