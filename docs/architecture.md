# System Architecture

## Overview

The UAV Emergency Rescue System is structured as a modular ROS2-based architecture where each subsystem communicates through well-defined topics and services. PX4 acts as the flight controller and connects to ROS2 via the micro-XRCE-DDS bridge.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Ground Side                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐   ┌───────────────┐  │
│  │  QGroundCtrl │    │  BeiDou SMS  │   │  RTK Base Stn │  │
│  │ (uav_control │    │  (beidou_sms)│   │  (rtk_pos.)   │  │
│  │    _gcs)     │    └──────┬───────┘   └──────┬────────┘  │
│  └──────┬───────┘           │                  │           │
└─────────┼───────────────────┼──────────────────┼───────────┘
          │ MAVLink/UDP        │ Coordinates       │ RTCM corrections
          │                   │                   │
┌─────────┼───────────────────┼──────────────────┼───────────┐
│         │              UAV Side                │           │
│  ┌──────▼───────┐    ┌──────▼───────┐   ┌──────▼────────┐  │
│  │   PX4 SITL   │◄──►│  ROS2 Bridge │   │  RTK Rover    │  │
│  │  (Autopilot) │    │ (micro-XRCE) │   │  (rtk_pos.)   │  │
│  └──────────────┘    └──────┬───────┘   └───────────────┘  │
│                             │                               │
│              ┌──────────────┼──────────────┐               │
│              │              │              │               │
│  ┌───────────▼──┐  ┌────────▼────┐  ┌─────▼──────────┐   │
│  │path_planning │  │   bringup   │  │target_tracking │   │
│  │  _rescue     │  │ (launcher)  │  │  _landing      │   │
│  └──────────────┘  └─────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## ROS2 Topic Map (Planned)

| Topic | Type | Publisher | Subscribers |
|-------|------|-----------|-------------|
| `/uav/rtk_pose` | `geometry_msgs/PoseStamped` | `rtk_positioning` | `path_planning_rescue`, `bringup` |
| `/uav/rtk_status` | `std_msgs/String` | `rtk_positioning` | `uav_control_gcs` |
| `/uav/target_pose` | `geometry_msgs/PoseStamped` | `target_tracking_landing` | `path_planning_rescue` |
| `/uav/mission_waypoints` | `custom` | `uav_control_gcs` | `path_planning_rescue` |
| `/beidou/rescue_coords` | `custom` | `beidou_sms` | `uav_control_gcs`, `path_planning_rescue` |
| `/px4/vehicle_odometry` | `px4_msgs/VehicleOdometry` | PX4 bridge | all modules |
| `/px4/trajectory_setpoint` | `px4_msgs/TrajectorySetpoint` | `path_planning_rescue` | PX4 bridge |

> Note: Custom message types will be defined in the `interfaces` package.

---

## PX4 Bridge

Communication between ROS2 and PX4 is handled through the micro-XRCE-DDS Agent:

```
PX4 (uXRCE-DDS client) <---> micro-XRCE-DDS Agent <---> ROS2 nodes
```

The agent must be running before any ROS2 nodes attempt to communicate with PX4.

---

## Integration Flow

1. BeiDou SMS module receives rescue coordinates from satellite network.
2. Coordinates are published to `/beidou/rescue_coords`.
3. `uav_control_gcs` loads or updates the mission waypoints.
4. RTK positioning provides high-precision pose throughout flight.
5. Path planning calculates obstacle-free routes to target.
6. Target tracking detects, tracks, and supports fixed-point landing.
7. All telemetry is relayed back to QGroundControl.

---

## TODO

- [ ] Finalize custom message types in `interfaces`
- [ ] Add sequence diagrams for mission execution flow
- [ ] Document PX4 parameter configuration for RTK
- [ ] Add figures under `docs/figures/`
