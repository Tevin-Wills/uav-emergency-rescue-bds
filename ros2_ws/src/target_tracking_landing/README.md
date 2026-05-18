# target_tracking_landing

**Owner:** Member 3  
**Responsibility:** Camera-based target detection, tracking, following, and fixed-point landing.

## Overview

This package processes onboard camera data to detect rescue targets, track and follow them during flight, and guide the UAV to a fixed-point precision landing over the target.

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/uav/target_pose` | `geometry_msgs/PoseStamped` | Estimated target position in world frame |
| `/uav/target_detected` | `std_msgs/Bool` | Target detection flag |

## Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/uav/rtk_pose` | `geometry_msgs/PoseStamped` | UAV position for target localisation |

## Package Structure

```
target_tracking_landing/
├── package.xml
├── CMakeLists.txt
├── src/
├── launch/
├── config/
├── docs/
└── README.md
```

## TODO

- [ ] Implement camera-based detection node
- [ ] Implement target tracking and following logic
- [ ] Implement fixed-point landing guidance
- [ ] Add launch file and camera configuration
