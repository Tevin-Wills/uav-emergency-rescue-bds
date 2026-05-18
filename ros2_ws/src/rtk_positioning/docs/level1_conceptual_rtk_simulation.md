# Level 1 Conceptual RTK Simulation

## Purpose

This document explains what the Level 1 RTK positioning simulation is, what it demonstrates, and how it fits into the broader UAV Emergency Rescue project.

---

## Background: What is RTK?

RTK (Real-Time Kinematic) is a satellite positioning technique that improves position accuracy from the standard GNSS range of 1–5 meters down to 2–5 centimetres.

It works by pairing two GNSS receivers:

```
Base station (fixed, known location)
        ↓
Sends RTCM correction data
        ↓
Rover (moving receiver — on the UAV)
        ↓
Applies corrections in real time
        ↓
Centimetre-level position output
```

The base station observes the same satellites as the rover. Because the base station's exact position is known, it can compute the error in the satellite signals and send correction data (RTCM format) to the rover. The rover uses these corrections to resolve carrier-phase ambiguities and produce a high-accuracy position.

RTK fix states:

| Status | Description | Typical Error |
|---|---|---|
| GNSS_ONLY | No correction applied | 1–5 m |
| RTK_FLOAT | Correction received, ambiguity not resolved | 0.2–0.5 m |
| RTK_FIXED | Full RTK fix, ambiguity resolved | 0.02–0.05 m |
| CORRECTION_LOST | Correction signal interrupted | 1–5 m |

---

## What Level 1 Is

Level 1 is a standalone ROS 2 software simulation of RTK positioning behavior.

It is designed to:

- Run without PX4, Gazebo, QGroundControl, or any hardware
- Demonstrate the improvement in position accuracy that RTK provides
- Produce ROS 2 topics that match the team interface contract
- Generate CSV logs for comparison and analysis
- Act as a verified base that Level 2 will extend

Level 1 treats:

- The UAV as the RTK rover
- A fixed coordinate as the RTK base station
- Gaussian noise reduction as the model for RTK correction behavior

---

## What Level 1 Is Not

Level 1 is **not** any of the following:

| What it is not | Why |
|---|---|
| Real RTK hardware | No physical receiver, antenna, or cable |
| Real RTCM processing | No RTCM bytes are generated, transmitted, or decoded |
| Real carrier-phase ambiguity resolution | Status transitions are time-based, not signal-based |
| Real BeiDou satellite RF simulation | No satellite orbital mechanics, signal propagation, or atmospheric modeling |
| PX4 GPS injection | No MAVLink GPS_RTCM_DATA messages are sent to PX4 |
| Claimed centimetre accuracy | Simulated noise values are models, not hardware measurements |

---

## Level 1 Node Architecture

```
┌─────────────────────┐
│  base_station_node  │──► /rtk/base_station (NavSatFix, 1 Hz)
└─────────────────────┘
                               │
┌─────────────────────┐        ▼
│  simulated_uav_node │──► /uav/ground_truth (Odometry, 10 Hz)
└─────────────────────┘        │
                               ▼
                  ┌────────────────────────┐
                  │  rtk_positioning_node  │
                  └────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    /uav/raw_gps   /uav/rtk_position  /uav/rtk_status
    (NavSatFix)    (NavSatFix)        (String)
                                          │
                                    /rtk/accuracy
                                    (Float32MultiArray)
                                          │
                  ┌───────────────────────┘
                  ▼
          ┌─────────────┐
          │ logger_node │──► results/logs/rtk_positioning/level1/*.csv
          └─────────────┘
```

---

## RTK Status Transitions in Level 1

Status transitions are time-based, controlled by `rtk_status_manager.py`:

```
Elapsed time    RTK status      Position noise
0 – 5 s         GNSS_ONLY       ±1.5 m (std)
5 – 15 s        RTK_FLOAT       ±0.25 m (std)
15 s +          RTK_FIXED       ±0.03 m (std)
```

This pattern repeats each time the simulation restarts. The transition is intentionally simple for Level 1 verification purposes.

---

## Expected Simulation Output

When Level 1 runs correctly, the CSV log should show:

```
Phase 1 (0–5 s):
  raw_gnss_std_m ≈ 1.5
  rtk_std_m      ≈ 1.5   (same — no correction yet)
  rtk_status     = GNSS_ONLY

Phase 2 (5–15 s):
  raw_gnss_std_m ≈ 1.5
  rtk_std_m      ≈ 0.25  (RTK correction active)
  rtk_status     = RTK_FLOAT

Phase 3 (15 s+):
  raw_gnss_std_m ≈ 1.5
  rtk_std_m      ≈ 0.03  (full RTK fix)
  rtk_status     = RTK_FIXED
  improvement    ≈ 98%
```

---

## Launch Command

```bash
source /opt/ros/jazzy/setup.bash
cd ~/uav-emergency-rescue-bds/ros2_ws
colcon build --packages-select rtk_positioning
source install/setup.bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

---

## Relationship to Level 2

Level 2 extends Level 1 by replacing `simulated_uav_node` with a PX4/Gazebo pose adapter and adding a simulated RTCM correction node. The core RTK logic (`gnss_noise_model`, `rtk_correction_model`, `coordinate_transform`, `rtk_status_manager`) is shared between both levels.

Level 1 must remain independently runnable after Level 2 is added.
