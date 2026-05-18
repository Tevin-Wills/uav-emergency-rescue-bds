# target_detection_tracking

**Owner:** Student 3
**Responsibility:** Camera-based target detection, tracking, following, and fixed-point landing.

## Overview

This package processes onboard camera data from Gazebo to detect rescue targets, track and follow them during flight, and guide the UAV to a fixed-point precision landing over the target.

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/target/detection` | `std_msgs/Bool` | `true` when target is detected |
| `/target/location` | `geometry_msgs/PoseStamped` | Estimated target position in world frame |

## Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/camera/image_raw` | `sensor_msgs/Image` | Raw camera feed from Gazebo |
| `/mission/status` | `std_msgs/String` | Activates detection at correct mission phase |

## Package Structure

```
target_detection_tracking/
├── package.xml
├── CMakeLists.txt
├── src/
├── launch/
├── config/
├── docs/
└── README.md
```

## Integration

- `path_planning` subscribes to `/target/location` for the final landing guidance phase.

See [`interfaces/integration_contract.md`](../../../../interfaces/integration_contract.md) for the full contract.

## TODO

- [ ] Implement camera-based detection node (e.g., using OpenCV or YOLO)
- [ ] Implement target tracking and following logic
- [ ] Implement fixed-point landing guidance
- [ ] Add launch file and camera configuration for Gazebo
