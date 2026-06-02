# rtk_positioning

**Owner:** Student 1 — Tevin Wills
**Module:** RTK GNSS Positioning

---

## Purpose

This package provides RTK GNSS positioning simulation for the UAV Emergency Rescue System. It delivers centimetre-level position topics that the broader system relies on for precision flight and landing.

The module is built in two levels:

| Level | What it proves | Needs PX4/Gazebo |
|---|---|---|
| Level 1 | RTK correction math works correctly in isolation | No |
| Level 2 | RTK module integrates with the team's simulation stack | Yes |

Both levels publish the same output topics. The difference is where the UAV position comes from and what drives the RTK status transitions.

---

## Level 1 — Standalone RTK Simulation

**Purpose:** Verify that the RTK correction algorithm works correctly, independently of PX4, Gazebo, or any team dependencies.

**What it proves:**
- Gaussian noise model correctly simulates raw GNSS error (~1.5 m std)
- RTK correction reduces positioning error to centimetre level (~0.03 m for RTK_FIXED)
- Status transitions (GNSS_ONLY → RTK_FLOAT → RTK_FIXED) are time-based and behave correctly
- All output topics publish in the correct ROS 2 message formats

**How it works:**
A synthetic UAV node generates a 50 m square flight path. The RTK positioning node adds Gaussian noise to produce a raw GNSS position, then applies correction noise to produce the RTK-corrected position. RTK status advances automatically based on elapsed time.

```
simulated_uav_node  →  /uav/ground_truth  →  rtk_positioning_node  →  output topics
```

**Launch:**
```bash
cd ~/uav-emergency-rescue-bds/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

**Output:**
```
results/logs/rtk_positioning/level1/rtk_level1_<timestamp>.csv   (18 columns)
```

---

## Level 2 — PX4/Gazebo-Integrated RTK Simulation

**Purpose:** Demonstrate that the RTK module works within the team's actual simulation stack, providing centimetre-level positioning during real autonomous UAV flight.

**What it proves:**
- UAV pose can be sourced from PX4/Gazebo instead of a synthetic path
- Centimetre-level accuracy is maintained during real simulated flight
- RTK status responds to simulated GPS_RTCM_DATA-style correction conditions
- The module publishes standard ROS 2 position topics for team integration

**How it works:**
The Gazebo navsat sensor provides real UAV GPS coordinates via ros_gz_bridge. A pose adapter converts those coordinates into the same `/uav/ground_truth` topic that Level 1 used, so the RTK core logic is unchanged. A simulated correction stream drives RTK status through realistic correction cycles.

```
Gazebo navsat sensor
        ↓
ros_gz_bridge  →  /gz/navsat
        ↓
px4_pose_adapter_node  →  /uav/ground_truth  →  rtk_positioning_node  →  output topics

rtcm_correction_simulator_node  →  /rtk/simulated_rtcm  →  rtk_positioning_node
```

**Simulated correction profile:**

| Time | Correction state | RTK status |
|---|---|---|
| 0–5 s | Not available | GNSS_ONLY |
| 5–15 s | Available, weak | RTK_FLOAT |
| 15–45 s | Available, strong | RTK_FIXED |
| 45–50 s | Lost | CORRECTION_LOST |
| 50+ s | Recovered | RTK_FIXED |

**Prerequisites:**
```bash
# Terminal 1 — start PX4 SITL + Gazebo first
~/launch_sim_24.sh
```

**Launch:**
```bash
# Terminal 2
cd ~/uav-emergency-rescue-bds/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch rtk_positioning level2_rtk_px4_sim.launch.py
```

**Output:**
```
results/logs/rtk_positioning/level2/rtk_level2_<timestamp>.csv   (22 columns)
```

---

## Published Topics

| Topic | Type | Level | Description |
|---|---|---|---|
| `/uav/rtk_position` | `sensor_msgs/msg/NavSatFix` | Both | RTK-corrected UAV position |
| `/uav/raw_gps` | `sensor_msgs/msg/NavSatFix` | Both | Raw GNSS position with noise |
| `/uav/rtk_status` | `std_msgs/msg/String` | Both | RTK fix state: `code\|name\|accuracy_m` |
| `/rtk/base_station` | `sensor_msgs/msg/NavSatFix` | Both | Fixed base station coordinate |
| `/uav/ground_truth` | `nav_msgs/msg/Odometry` | Both | UAV true position (synthetic L1 / Gazebo L2) |
| `/rtk/accuracy` | `std_msgs/msg/Float32MultiArray` | Both | `[raw_std_m, rtk_std_m, improvement_pct]` |
| `/rtk/error_metrics` | `std_msgs/msg/Float32MultiArray` | Both | `[raw_gnss_error_m, rtk_error_m]` |
| `/rtk/simulated_rtcm` | `interfaces/msg/SimulatedRtcm` | Level 2 | Simulated correction stream |

---

## Package Structure

```
rtk_positioning/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/
│   └── rtk_positioning
├── src/
│   └── rtk_positioning/
│       ├── __init__.py
│       ├── gnss_noise_model.py                  # shared core — both levels
│       ├── rtk_correction_model.py              # shared core — both levels
│       ├── coordinate_transform.py              # shared core — both levels
│       ├── rtk_status_manager.py                # shared core — both levels
│       ├── base_station_node.py                 # shared — both levels
│       ├── rtk_positioning_node.py              # shared — both levels (mode via parameter)
│       ├── logger_node.py                       # shared — both levels (mode via parameter)
│       ├── simulated_uav_node.py                # Level 1 only
│       ├── px4_pose_adapter_node.py             # Level 2 only
│       └── rtcm_correction_simulator_node.py    # Level 2 only
├── launch/
│   ├── level1_rtk_sim.launch.py
│   └── level2_rtk_px4_sim.launch.py
├── config/
│   ├── base_station.yaml
│   ├── noise_profiles.yaml
│   ├── level1_rtk_params.yaml
│   └── level2_rtk_params.yaml
└── docs/
    ├── LEVEL1_IMPLEMENTATION_PLAN.md
    ├── LEVEL2_IMPLEMENTATION_PLAN.md
    ├── CLAUDE_LEVEL1_PROMPT.md
    ├── CLAUDE_LEVEL2_PROMPT.md
    ├── level1_conceptual_rtk_simulation.md
    ├── level2_mavlink_aware_rtk_simulation.md
    ├── level2_px4_integration_notes.md
    ├── rtk_topic_interface.md
    └── simulation_assumptions.md
```

---

## Results Output

```
results/logs/rtk_positioning/level1/     ← Level 1 CSV logs  (18 columns)
results/logs/rtk_positioning/level2/     ← Level 2 CSV logs  (22 columns)
results/graphs/rtk_positioning/level1/   ← Level 1 graphs
results/graphs/rtk_positioning/level2/   ← Level 2 graphs
```

---

## Simulation Boundaries

Both levels are software simulations. Neither level uses:
- Real RTK hardware (base station or rover receiver)
- Real RTCM binary correction data
- Real BeiDou or GPS satellite RF signals
- Real MAVLink GPS_RTCM_DATA injection into PX4

Level 2 connects to the real PX4/Gazebo simulation stack but models correction behavior through a simulated correction quality stream, not through real RTCM processing.
