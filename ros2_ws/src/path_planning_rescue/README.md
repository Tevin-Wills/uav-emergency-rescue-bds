# path_planning_rescue

**Owner:** Member 4  
**Responsibility:** Autonomous obstacle avoidance and mission route planning.

## Overview

This package plans safe, obstacle-free routes from the UAV's current position to the rescue target. It dynamically updates the trajectory in response to detected obstacles and publishes setpoints to PX4.

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/px4/trajectory_setpoint` | `px4_msgs/TrajectorySetpoint` | Planned trajectory setpoints for PX4 |

## Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/uav/rtk_pose` | `geometry_msgs/PoseStamped` | Current UAV position |
| `/uav/target_pose` | `geometry_msgs/PoseStamped` | Target location from tracking module |
| `/uav/mission_waypoints` | TBD | Mission waypoints from GCS |

## Package Structure

```
path_planning_rescue/
├── package.xml
├── CMakeLists.txt
├── src/
├── launch/
├── config/
├── docs/
└── README.md
```

## TODO

- [ ] Implement path planning algorithm (e.g., A*, RRT)
- [ ] Integrate obstacle detection input
- [ ] Publish trajectory setpoints to PX4
- [ ] Add simulation test scenarios
