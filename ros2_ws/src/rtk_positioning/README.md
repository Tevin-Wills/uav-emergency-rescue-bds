# rtk_positioning

**Owner:** Student 1 — Tevin Wills
**Module:** RTK GNSS Positioning

## Overview

This package provides RTK GNSS positioning simulation for the UAV Emergency Rescue System.

Level 1 is a standalone ROS 2 simulation. It demonstrates RTK correction behavior by comparing raw GNSS positioning with RTK-corrected positioning using a simulated moving UAV and a fixed base station.

Level 1 does not use PX4, Gazebo, QGroundControl, MAVLink, real RTCM data, or real RTK hardware.

## Published Topics

| Topic | Type | Description |
|---|---|---|
| `/uav/raw_gps` | `sensor_msgs/msg/NavSatFix` | Simulated raw GNSS position with larger noise |
| `/uav/rtk_position` | `sensor_msgs/msg/NavSatFix` | Simulated RTK-corrected position with smaller noise |
| `/uav/rtk_status` | `std_msgs/msg/String` (Level 1) | RTK fix status: GNSS_ONLY, RTK_FLOAT, RTK_FIXED |
| `/rtk/base_station` | `sensor_msgs/msg/NavSatFix` | Fixed base station coordinate |
| `/uav/ground_truth` | `nav_msgs/msg/Odometry` | Simulated UAV true position |
| `/rtk/accuracy` | `std_msgs/msg/Float32MultiArray` (Level 1) | Error and accuracy metrics |

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
│       ├── gnss_noise_model.py
│       ├── rtk_correction_model.py
│       ├── coordinate_transform.py
│       ├── rtk_status_manager.py
│       ├── base_station_node.py
│       ├── simulated_uav_node.py
│       ├── rtk_positioning_node.py
│       └── logger_node.py
├── launch/
│   └── level1_rtk_sim.launch.py
├── config/
│   ├── base_station.yaml
│   ├── noise_profiles.yaml
│   └── level1_rtk_params.yaml
├── msg/
│   ├── RtkStatus.msg
│   └── RtkAccuracy.msg
└── docs/
    ├── LEVEL1_IMPLEMENTATION_PLAN.md
    ├── CLAUDE_LEVEL1_PROMPT.md
    ├── level1_conceptual_rtk_simulation.md
    ├── rtk_topic_interface.md
    └── simulation_assumptions.md
```

## Launch

```bash
cd ros2_ws
colcon build --packages-select rtk_positioning
source install/setup.bash
ros2 launch rtk_positioning level1_rtk_sim.launch.py
```

## Results Output

```
results/logs/rtk_positioning/level1/
results/graphs/rtk_positioning/level1/
```
