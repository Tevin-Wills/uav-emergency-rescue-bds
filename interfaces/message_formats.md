# Message Formats

## Purpose

This file defines the message structures exchanged between modules. It documents the
**messages actually implemented** (standard ROS 2 types plus the two custom types in the
`interfaces` package), verified against the node source. Topic names and publisher/subscriber
wiring are in [`ros2_topics.md`](ros2_topics.md); coordinate conventions are in
[`coordinate_format.md`](coordinate_format.md).

> Earlier drafts of this file described JSON payloads; the system uses native ROS 2 messages.
> Standard ROS types are used wherever possible to avoid custom dependencies.

---

## 1. UAV Position — `sensor_msgs/NavSatFix`

Topic: `/uav/rtk_position` (RTK-corrected) and `/uav/raw_gps` (raw). Published by
`rtk_positioning`; subscribed by `path_planning`, `target_detection_tracking`.

Standard `NavSatFix`: `header`, `status`, `latitude`, `longitude`, `altitude` (WGS-84,
metres), and `position_covariance`. The fix-quality label is carried separately on
`/uav/rtk_status` (below) rather than overloading `NavSatFix.status`.

---

## 2. RTK Status — `std_msgs/String`

Topic: `/uav/rtk_status`. Published by `rtk_positioning`; subscribed by `qgc_control`,
`target_detection_tracking`.

Format: `code|name|sigma_m`, e.g. `3|RTK_FIXED|0.032`.

| Field | Meaning |
|---|---|
| `code` | numeric fix code |
| `name` | `RTK_FIXED`, `RTK_FLOAT`, `GNSS_ONLY`, or `NO_FIX` |
| `sigma_m` | reported 1-σ horizontal accuracy in metres |

---

## 3. RTK Mission Viability — `std_msgs/String`

Topic: `/rtk/mission_viability`. Published by `rtk_positioning`; subscribed by `qgc_control`.
The RTK-accuracy gate that governs the precision landing. Values include `LANDING_VIABLE`
and `APPROACH_VIABLE` (degraded states hold/abort the landing).

Companion numeric RTK topics: `/rtk/accuracy` and `/rtk/error_metrics`
(`std_msgs/Float32MultiArray`), `/rtk/baseline_km` (`std_msgs/Float32`).

---

## 4. Simulated RTCM — `interfaces/SimulatedRtcm`

Topic: `/rtk/simulated_rtcm`. Internal to `rtk_positioning` (the simulated correction stream
that drives the FIXED→FLOAT→GNSS degradation model). Definition
(`ros2_ws/src/interfaces/msg/SimulatedRtcm.msg`):

```
std_msgs/Header header
uint8   sequence_id
uint8   fragment_id
bool    fragmented
uint16  length
bool    correction_available
float32 correction_age_sec
float32 correction_quality
string  correction_source
float32 gnss_noise_std_m
```

---

## 5. Emergency Target Coordinate — `interfaces/EmergencyCoordinate`

Topic: `/target/emergency_coordinate`. Published by `beidou_short_message`; subscribed by
`qgc_control`, `path_planning`. Definition
(`ros2_ws/src/interfaces/msg/EmergencyCoordinate.msg`):

```
std_msgs/Header header
float64 latitude        # decimal degrees (WGS-84)
float64 longitude       # decimal degrees (WGS-84)
string  source_id       # BeiDou terminal / destination ID that sent the message
string  raw_message     # original decoded short message
```

---

## 6. BeiDou Short Message — `std_msgs/String`

Topic: `/rescue/beidou_message`. Published by `beidou_short_message`. The raw decoded
short-message text (the structured coordinate is published separately as
`EmergencyCoordinate` above).

---

## 7. Target Detection — `std_msgs/Bool` + `geometry_msgs/PoseStamped`

Published by `target_detection_tracking`; subscribed by `path_planning` (and `qgc_control`
for the detection flag).

- `/target/detection` — `std_msgs/Bool` — `true` when a target is currently detected.
- `/target/location` — `geometry_msgs/PoseStamped` — target pose in the `px4_local_enu` frame.

---

## 8. Path Planning Output — `nav_msgs/Path`

- `/planner/path` — `nav_msgs/Path` — planned obstacle-free path. Published by `path_planning`;
  subscribed by `qgc_control`.
- `/map/obstacles` — `nav_msgs/OccupancyGrid` (latched) — obstacle map used for planning.

---

## 9. Mission Status & Waypoints

Published by `mission_status_node` (inside the `qgc_control` package); subscribed by all
modules / `path_planning`.

- `/mission/status` — `std_msgs/String` — current phase. Phase values:
  `IDLE`, `DISTRESS_RECEIVED`, `MISSION_PLANNED`, `IN_FLIGHT`, `TARGET_ACQUIRED`, `LANDING`,
  `LANDING_HOLD`, `LANDING_VIABLE`, `COMPLETE`, `ABORTED`.
- `/mission/waypoints` — `nav_msgs/Path` (latched) — mission waypoints for `path_planning`.
- `/uav/telemetry` — `std_msgs/String` — aggregated phase + RTK quality for operators.

---

## Notes

- Coordinates use WGS-84 decimal degrees throughout. See [`coordinate_format.md`](coordinate_format.md).
- All custom `.msg` definitions live in `ros2_ws/src/interfaces/msg/`.
- Update this file whenever a message format changes — all team members must be notified.
