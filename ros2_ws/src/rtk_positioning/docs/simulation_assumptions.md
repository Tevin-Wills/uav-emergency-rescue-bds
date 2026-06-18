# Level 1 & 2 Simulation Assumptions

This document explicitly lists all assumptions and simplifications made in the RTK positioning
simulation. Sections 1–10 describe the Level 1 model; **all of them carry forward into Level 2
unchanged** except where the Level 2 Addendum (Section 11) states otherwise. Any user of this
module must understand these before interpreting results.

---

## 1. RTK Model Assumption

**Assumption:** RTK correction is modelled as a reduction in Gaussian position noise, not as real carrier-phase processing.

**What this means:**

In real RTK, the base station sends raw RTCM correction bytes. The rover receiver uses these bytes alongside its own carrier-phase measurements to resolve integer ambiguities and produce a centimetre-level position.

In Level 1, "correction" simply means: when RTK status is RTK_FIXED, a smaller noise standard deviation (0.03 m) is applied to the true position instead of the standard GNSS noise (1.5 m).

**What cannot be claimed:** real carrier-phase ambiguity resolution has occurred.

---

## 2. RTK Status Transition Assumption

**Assumption:** RTK status transitions are time-based, not signal-based.

| Time window | Status |
|---|---|
| 0 – 5 seconds | GNSS_ONLY |
| 5 – 15 seconds | RTK_FLOAT |
| 15 seconds onward | RTK_FIXED |

**What this means:** In a real receiver, the transition to RTK_FLOAT requires receiving RTCM correction data from the base station, and the transition to RTK_FIXED requires resolving carrier-phase integer ambiguities — a process that depends on satellite geometry, multipath, and signal quality. Level 1 does none of this.

**What cannot be claimed:** the simulation shows real RTK convergence behavior.

---

## 3. Coordinate Transform Assumption

**Assumption:** A flat-earth local tangent plane approximation is used to convert ENU meter offsets to WGS84 latitude/longitude.

**Formula used:**

```
lat = base_lat + north_m / 111320
lon = base_lon + east_m  / (111320 * cos(base_lat))
alt = base_alt + up_m
```

**Valid range:** This approximation is accurate to within 0.1% for distances up to approximately 1 km from the base station. The Level 1 square-search path spans 50 m × 50 m, well within this range.

**What cannot be claimed:** geodetically rigorous coordinate transformations (ellipsoid model, datum corrections) are applied.

---

## 4. UAV Path Assumption

**Assumption:** The UAV follows a simple, repeating square-search path at a fixed altitude.

**Path parameters (defaults):**

```
Leg length:      50 m
Speed:           5 m/s
Flight altitude: 30 m AGL
Path cycle:      40 seconds (4 legs × 10 s each)
```

**What this means:** The path is deterministic and repeatable. It does not represent real UAV flight dynamics, wind effects, or attitude changes.

**What cannot be claimed:** real UAV flight behavior is simulated.

---

## 5. Noise Model Assumption

**Assumption:** Position noise is modelled as independent Gaussian noise applied separately to x, y, and z axes in ENU space.

**Standard deviations used:**

```
GNSS_ONLY:       1.5 m
RTK_FLOAT:       0.25 m
RTK_FIXED:       0.03 m
CORRECTION_LOST: 2.5 m
```

**What this means:** Real GNSS errors include correlated components such as ionospheric delay, tropospheric delay, multipath, satellite geometry (DOP), and clock drift. These are not modelled. Gaussian noise is a reasonable first-order approximation for a software behavior demonstration.

**What cannot be claimed:** the error model is physically accurate.

---

## 6. Base Station Assumption

**Assumption:** The base station is a fixed, known coordinate. It does not move, and its position is perfectly known.

**Default coordinate:**

```
Latitude:  39.981000° (Beijing area reference)
Longitude: 116.344000°
Altitude:  50.0 m
```

**What this means:** In a real deployment, the base station position must be surveyed to centimetre accuracy. Level 1 uses a hardcoded coordinate for simulation purposes only.

---

## 7. No PX4, Gazebo, or MAVLink

**Assumption:** Level 1 runs completely independently of PX4, Gazebo, and QGroundControl.

No PX4 topics are subscribed to or published. No MAVLink messages are sent. No Gazebo simulation is required. The simulated UAV path is generated internally by `simulated_uav_node`.

This is intentional — Level 1 validates the RTK module logic in isolation before integrating with the full simulation stack in Level 2.

---

## 8. No Real BeiDou Signal Processing

**Assumption:** No BeiDou (or GPS) satellite signals, orbital mechanics, or RF propagation are simulated.

The project uses BeiDou-compatible RTK receivers in the intended hardware deployment. Level 1 does not differentiate between GPS and BeiDou signal sources. The noise model applies equally regardless of the satellite constellation.

---

## 9. CSV Log Path Assumption

**Assumption:** The logger node writes to an absolute path derived from the user's home directory:

```
~/uav-emergency-rescue-bds/results/logs/rtk_positioning/level1/
```

If the repository is cloned to a different location, the `log_directory` parameter must be overridden in the launch file or via the command line:

```bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py \
  logger_node:log_directory:=/path/to/results/logs/rtk_positioning/level1
```

---

## 10. Level 1 is Designed to be Extended

Level 1 is explicitly a foundation. The following items are out of scope for Level 1 but are the target of Level 2:

```
PX4/Gazebo pose adapter
Simulated RTCM correction message behavior
Correction quality, delay, and loss modeling
MAVLink-aware integration
Level 2 launch file and logging
```

Level 1 files must not be deleted or broken when Level 2 is added.

---

## 11. Level 2 Addendum

Level 2 sources the UAV pose from the PX4/Gazebo simulation (via `ros_gz_bridge`) and drives RTK
status from simulated correction-message quality rather than a hard-coded clock. The following
clarifications apply on top of Sections 1–10.

### 11.1 Status is correction-quality-driven, but the quality is still scripted

**Assumption:** In Level 2, `rtk_positioning_node` derives RTK status from the
`correction_quality` / `correction_available` fields of the `SimulatedRtcm` message (thresholds:
Float ≥ 0.4, Fixed ≥ 0.8, timeout 2.0 s) — *not* from the Level 1 time table in Section 2.

**What this means:** the status logic itself reacts to correction conditions. **However**, those
conditions are emitted by `rtcm_correction_simulator_node` on a **fixed scripted timeline**
(0–5 s unavailable → 5–15 s quality 0.5 → 15–45 s quality 0.95 → 45–50 s lost → 50 s+ recovered).
So the GNSS→Float→Fixed convergence and the correction-loss/recovery event still occur at
**pre-set times**, not because of real satellite geometry or carrier-phase ambiguity resolution.

**What cannot be claimed:** that Level 2 shows real RTK convergence behaviour. The convergence
timing is a design choice (same caveat as Section 2).

### 11.2 Initialization happens on the ground, before the flight

In the analysed run the logger started ~7 minutes before take-off (take-off at t ≈ 497 s of a
1028 s log). The entire scripted initialization sequence (convergence + the correction-loss
event, t < 50 s) therefore occurs while the vehicle is **stationary on the ground**. The Level 2
analysis treats this window as an **initialization / state-machine demonstration** and reports
in-flight positioning accuracy **separately** (from the airborne window). The whole-log mean is
*not* used as the accuracy result. In-flight resilience to a mid-mission correction loss is
delegated to Level 3.

### 11.3 Fictional base-station coordinate vs the real Gazebo world origin

The ENU base station remains the Section 6 Beijing reference (39.981000°, 116.344000°), but the
real PX4/Gazebo flight runs at the default world origin near **ETH Zürich (≈47.3980°, 8.5462°)**.
Positioning **errors** are computed in metres within a local ENU frame, and the forward
(ENU→lat/lon) and inverse (lat/lon→ENU) transforms cancel, so the Beijing base is **harmless for
the metre-based error metrics and the trajectory overlay**. Only the absolute latitude/longitude
written to the CSV are fictional; they should not be interpreted as the physical flight location.
