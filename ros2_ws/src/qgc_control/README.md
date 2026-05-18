# qgc_control

**Owner:** Student 2
**Responsibility:** UAV control via QGroundControl and MAVLink telemetry management.

## Overview

This package manages the command and telemetry flow between QGroundControl, ROS 2, and PX4. It handles mission upload, telemetry parsing, and mission status broadcasting.

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/mission/waypoints` | Custom | Current mission waypoints |
| `/mission/status` | `std_msgs/String` | Current mission phase |
| `/uav/telemetry` | Custom | Aggregated UAV telemetry status |

## Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/target/emergency_coordinate` | Custom | Incoming rescue coordinate from beidou_short_message |
| `/uav/rtk_status` | `std_msgs/String` | RTK fix status for GCS display |

## Package Structure

```
qgc_control/
├── package.xml
├── CMakeLists.txt
├── src/
├── launch/
├── config/
├── docs/
└── README.md
```

## Integration

- Receives rescue coordinate from `beidou_short_message`.
- Provides mission waypoints to `path_planning`.
- Broadcasts mission status to all modules.

See [`interfaces/integration_contract.md`](../../../../interfaces/integration_contract.md) for the full contract.

## TODO

- [ ] Implement MAVLink / QGC bridge node
- [ ] Handle mission upload from BeiDou emergency coordinate
- [ ] Broadcast `/mission/status` throughout mission phases
- [ ] Forward telemetry to operator display
- [ ] Add launch file
