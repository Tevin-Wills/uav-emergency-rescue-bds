# uav_control_gcs

**Owner:** Member 2  
**Responsibility:** UAV control via QGroundControl and MAVLink telemetry management.

## Overview

This package manages the command and telemetry flow between QGroundControl, ROS2, and PX4. It handles mission upload, telemetry parsing, and operator command forwarding.

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/uav/mission_waypoints` | TBD | Current mission waypoints |
| `/uav/telemetry_status` | TBD | Aggregated telemetry status |

## Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/beidou/rescue_coords` | TBD | Incoming rescue coordinates from BeiDou |
| `/uav/rtk_status` | `std_msgs/String` | RTK fix status for GCS display |

## Package Structure

```
uav_control_gcs/
├── package.xml
├── CMakeLists.txt
├── src/
├── launch/
├── config/
├── docs/
└── README.md
```

## TODO

- [ ] Implement MAVLink/QGC bridge node
- [ ] Handle mission upload from BeiDou coordinates
- [ ] Forward telemetry to operator display
- [ ] Add launch file
