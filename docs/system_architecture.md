# System Architecture

## Overview

The UAV Emergency Rescue System is structured as a modular ROS 2-based architecture where each subsystem communicates through well-defined topics and services. PX4 acts as the flight controller and connects to ROS 2 via the micro-XRCE-DDS bridge.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Ground Side                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐   ┌───────────────┐  │
│  │  QGroundCtrl │    │  BeiDou SMS  │   │  RTK Base Stn │  │
│  │ (qgc_control)│    │  (beidou_    │   │  (rtk_pos.)   │  │
│  │              │    │  short_msg)  │   └──────┬────────┘  │
│  └──────┬───────┘    └──────┬───────┘          │           │
└─────────┼───────────────────┼──────────────────┼───────────┘
          │ MAVLink/UDP        │ Coordinates       │ RTCM corrections
          │                   │                   │
┌─────────┼───────────────────┼──────────────────┼───────────┐
│         │              UAV Side                │           │
│  ┌──────▼───────┐    ┌──────▼───────┐   ┌──────▼────────┐  │
│  │   PX4 SITL   │◄──►│  ROS 2 Bridge│   │  RTK Rover    │  │
│  │  (Autopilot) │    │ (micro-XRCE) │   │  (rtk_pos.)   │  │
│  └──────────────┘    └──────┬───────┘   └───────────────┘  │
│                             │                               │
│              ┌──────────────┼──────────────┐               │
│              │              │              │               │
│  ┌───────────▼──┐  ┌────────▼────┐  ┌─────▼──────────┐   │
│  │ path_planning│  │   bringup   │  │target_detection│   │
│  │              │  │ (launcher)  │  │  _tracking     │   │
│  └──────────────┘  └─────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## System Workflow

```
BeiDou emergency coordinate
        ↓
beidou_short_message → /target/emergency_coordinate
        ↓
qgc_control (QGroundControl + MAVLink)
        ↓  /mission/waypoints
path_planning module
        ↓  /fmu/in/trajectory_setpoint
PX4 SITL (Autopilot)
        ↓
Gazebo Harmonic (3D simulation)
        ↓
rtk_positioning + target_detection_tracking
        ↓
Rescue feedback to ground station
```

---

## ROS 2 Topic Map

| Topic | Type | Publisher | Subscribers |
|-------|------|-----------|-------------|
| `/uav/rtk_position` | `geometry_msgs/PoseStamped` | `rtk_positioning` | `path_planning`, `qgc_control` |
| `/uav/rtk_status` | `std_msgs/String` | `rtk_positioning` | `qgc_control` |
| `/target/location` | `geometry_msgs/PoseStamped` | `target_detection_tracking` | `path_planning` |
| `/mission/waypoints` | custom | `qgc_control` | `path_planning` |
| `/target/emergency_coordinate` | custom | `beidou_short_message` | `qgc_control`, `path_planning` |
| `/fmu/out/vehicle_odometry` | `px4_msgs/VehicleOdometry` | PX4 bridge | all modules |
| `/fmu/in/trajectory_setpoint` | `px4_msgs/TrajectorySetpoint` | `path_planning` | PX4 bridge |

Full topic definitions: [`interfaces/ros2_topics.md`](../interfaces/ros2_topics.md)

> Custom message types are defined in `ros2_ws/src/interfaces/`.

---

## PX4 Bridge

Communication between ROS 2 and PX4 is handled through the micro-XRCE-DDS Agent:

```
PX4 (uXRCE-DDS client) <---> micro-XRCE-DDS Agent <---> ROS 2 nodes
```

The agent must be running before any ROS 2 nodes attempt to communicate with PX4.

---

## Integration Flow

1. BeiDou short message module receives rescue coordinates from satellite network (simulated).
2. Coordinates are published to `/target/emergency_coordinate`.
3. `qgc_control` loads or updates the mission waypoints.
4. RTK positioning provides high-precision pose throughout flight.
5. Path planning calculates obstacle-free routes to target.
6. Target detection and tracking detects, tracks, and supports fixed-point landing.
7. All telemetry is relayed back to QGroundControl.

---

## TODO

- [ ] Finalize custom message types in `ros2_ws/src/interfaces/`
- [ ] Add sequence diagrams for mission execution flow
- [ ] Document PX4 parameter configuration for RTK
- [ ] Add figures under `docs/figures/`
