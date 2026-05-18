# rtk_positioning

**Owner:** Member 1  
**Responsibility:** High-precision RTK GNSS positioning for the UAV.

## Overview

This package integrates an RTK GNSS base-rover setup with PX4 to provide centimetre-level positioning throughout the full UAV flight. It exposes ROS2 topics for position and status that other modules consume.

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/uav/rtk_pose` | `geometry_msgs/PoseStamped` | High-precision RTK position and orientation |
| `/uav/rtk_status` | `std_msgs/String` | RTK fix status (FLOAT, FIX, NONE) |

## Package Structure

```
rtk_positioning/
├── package.xml
├── CMakeLists.txt
├── src/          # C++ / Python source nodes
├── launch/       # Launch files
├── config/       # RTK hardware and driver config
├── msg/          # Custom messages (if needed)
├── docs/
│   ├── design.md
│   ├── rtk_architecture.md
│   └── experiments.md
└── README.md
```

## TODO

- [ ] Implement RTK GNSS driver node
- [ ] Configure base-rover RTCM correction pipeline
- [ ] Integrate corrections into PX4 EKF2
- [ ] Add launch file for simulation and hardware
- [ ] Document hardware wiring and parameter setup in `docs/`
