# Level 1 Simulation Assumptions

This document explicitly lists all assumptions and simplifications made in the Level 1 RTK positioning simulation. Any user of this module must understand these before interpreting results.

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
