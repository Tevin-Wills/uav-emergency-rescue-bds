# path_planning

**Owner:** Student 4
**Responsibility:** Autonomous obstacle avoidance and mission route planning.

## Overview

This package plans safe, obstacle-free routes from the UAV's current position to the rescue target. It dynamically updates the trajectory in response to detected obstacles and publishes setpoints directly to PX4.

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/planner/path` | Custom | Planned obstacle-free path |
| `/fmu/in/trajectory_setpoint` | `px4_msgs/TrajectorySetpoint` | Trajectory setpoints sent to PX4 |

## Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/uav/rtk_position` | `geometry_msgs/PoseStamped` | Current UAV position from rtk_positioning |
| `/target/location` | `geometry_msgs/PoseStamped` | Target location from target_detection_tracking |
| `/mission/waypoints` | Custom | Mission waypoints from qgc_control |

## Package Structure

```
path_planning/
├── package.xml
├── CMakeLists.txt
├── src/
├── launch/
├── config/
├── docs/
└── README.md
```

## Integration

- Receives position from `rtk_positioning`.
- Receives target location from `target_detection_tracking`.
- Receives mission from `qgc_control`.
- Sends trajectory setpoints directly to PX4 via the micro-XRCE-DDS bridge.

See [`interfaces/integration_contract.md`](../../../../interfaces/integration_contract.md) for the full contract.

## TODO

- [ ] Implement path planning algorithm (e.g., A*, RRT, or Dijkstra)
- [ ] Integrate obstacle detection input
- [ ] Publish trajectory setpoints to `/fmu/in/trajectory_setpoint`
- [ ] Add simulation test scenarios and sample data
