# Level 2 MAVLink-Aware RTK Simulation

## 1. Purpose

Level 2 extends the standalone Level 1 RTK simulation by:

- Replacing the synthetic UAV path with real UAV pose from PX4/Gazebo
- Replacing time-based RTK status transitions with correction-message-driven transitions

Level 2 is still a software simulation. It does not use real RTK hardware, does not decode real RTCM binary data, and does not simulate real BeiDou or GPS satellite RF signals.

---

## 2. What GPS_RTCM_DATA-Style Means

In a real PX4 RTK workflow, the base station sends RTCM correction data through QGroundControl via the MAVLink `GPS_RTCM_DATA` message to the UAV's GNSS receiver. The receiver uses this data to resolve carrier-phase ambiguities and achieve centimeter-level accuracy.

Level 2 does not implement this real pathway. Instead it models the *behavior* of that correction transport:

| Real system | Level 2 simulation |
|---|---|
| RTCM binary stream from base station | `SimulatedRtcm` message with quality/availability fields |
| MAVLink `GPS_RTCM_DATA` packets | `/rtk/simulated_rtcm` ROS 2 topic |
| Carrier-phase ambiguity resolution | Quality threshold checks (`float_quality_threshold`, `fixed_quality_threshold`) |
| Correction loss due to link failure | `correction_available=False` with growing `correction_age_sec` |

---

## 3. Simulated Correction Profile

The `rtcm_correction_simulator_node` publishes the following correction pattern at 5 Hz:

| Time window | `correction_available` | `correction_quality` | Expected RTK status |
|---|---|---|---|
| 0–5 s | False | 0.00 | `GNSS_ONLY` |
| 5–15 s | True | 0.50 | `RTK_FLOAT` |
| 15–45 s | True | 0.95 | `RTK_FIXED` |
| 45–50 s | False | 0.00 | `CORRECTION_LOST` |
| 50+ s | True | 0.95 | `RTK_FIXED` (recovery) |

`correction_age_sec` grows during periods when `correction_available=False`, simulating how stale the last correction data has become.

---

## 4. RTK Status Decision Logic

The `rtk_positioning_node` uses the following logic in Level 2 mode (`use_simulated_rtcm=True`):

```
No RTCM message received yet:
    → GNSS_ONLY

Last RTCM message older than correction_timeout_sec (2.0 s):
    → CORRECTION_LOST

correction_available = False, never had corrections before:
    → GNSS_ONLY

correction_available = False, had corrections before:
    → CORRECTION_LOST

correction_available = True, quality >= fixed_quality_threshold (0.8):
    → RTK_FIXED

correction_available = True, quality >= float_quality_threshold (0.4):
    → RTK_FLOAT

correction_available = True, quality < float_quality_threshold:
    → GNSS_ONLY
```

The noise applied to the GPS position matches the status:

| Status | Noise std (m) | Meaning |
|---|---|---|
| `GNSS_ONLY` | 1.5 | Standard GNSS accuracy |
| `RTK_FLOAT` | 0.25 | Partial correction, ambiguity not resolved |
| `RTK_FIXED` | 0.03 | Full RTK correction |
| `CORRECTION_LOST` | 2.5 | Degraded — was corrected, now link lost |

---

## 5. SimulatedRtcm Message

Defined in `ros2_ws/src/interfaces/msg/SimulatedRtcm.msg`:

| Field | Type | Meaning |
|---|---|---|
| `header` | `std_msgs/Header` | Timestamp and frame |
| `sequence_id` | `uint8` | Simulated message sequence (wraps at 255) |
| `fragment_id` | `uint8` | Always 0 (no fragmentation at 120 bytes) |
| `fragmented` | `bool` | Always False |
| `length` | `uint16` | Simulated payload bytes (120 when available, 0 when not) |
| `correction_available` | `bool` | Whether correction is currently active |
| `correction_age_sec` | `float32` | Seconds since corrections were last available |
| `correction_quality` | `float32` | Quality score 0.0–1.0 |
| `correction_source` | `string` | Always `"simulated_base_station"` |

This message is not real RTCM. It does not contain binary correction data.

---

## 6. What Can Be Claimed After Level 2

**Can claim:**
- The RTK module was extended from standalone simulation to PX4/Gazebo-aware simulation
- The UAV pose is sourced from the Gazebo simulation via the ros_gz_bridge navsat sensor
- The module simulates GPS_RTCM_DATA-style correction behavior through quality, availability, and loss events
- RTK status transitions realistically between GNSS_ONLY, RTK_FLOAT, RTK_FIXED, and CORRECTION_LOST
- The module is structured for future real RTK hardware integration

**Cannot claim:**
- Real RTCM binary data was decoded
- Real MAVLink GPS_RTCM_DATA was injected into PX4
- Real carrier-phase ambiguity resolution was performed
- Real centimeter-level hardware accuracy was demonstrated
- Real BeiDou satellite signals were simulated
