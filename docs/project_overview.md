# Project Overview

## Project Title

UAV Emergency Rescue System Based on BeiDou Navigation and Short Message Communication

---

## Background

Natural disasters — earthquakes, floods, landslides — frequently leave survivors isolated in locations that are difficult or dangerous for human rescue teams to reach quickly. Timely location of survivors and rapid delivery of initial aid are critical to improving survival rates.

Unmanned Aerial Vehicles (UAVs) have emerged as a powerful tool for emergency response. Their ability to cover terrain rapidly, operate in areas inaccessible to ground vehicles, and carry sensors for victim detection makes them well-suited for rescue support missions.

---

## Why UAVs in Disaster Response

- **Speed:** UAVs can be deployed in minutes and cover wide search areas faster than ground teams.
- **Access:** UAVs fly over debris, flooded roads, and unstable terrain that blocks ground vehicles.
- **Sensors:** Cameras, thermal imagers, and GPS receivers on UAVs locate survivors and assess damage.
- **Communication:** UAVs can serve as aerial relay nodes for communication in areas where infrastructure is destroyed.

---

## Why BeiDou and GNSS Matter

Standard GPS alone is insufficient for precision rescue operations:

- **BeiDou Short Message Service (SMS):** China's BeiDou satellite navigation system includes a unique two-way short message capability. Survivors or ground units can send emergency coordinates directly via satellite, bypassing destroyed terrestrial communication infrastructure.
- **RTK GNSS:** Real-Time Kinematic positioning combines a base station and rover to achieve centimetre-level accuracy — critical for precise landing at a rescue target and for accurate path planning in complex terrain.

---

## Project Purpose

This project builds a simulation-based integrated UAV emergency rescue system that demonstrates:

1. Receiving rescue coordinates via BeiDou short message communication.
2. Planning an obstacle-free autonomous flight path to the target.
3. Maintaining centimetre-level positioning accuracy throughout the mission using RTK GNSS.
4. Detecting and tracking the rescue target using onboard camera.
5. Executing a precision fixed-point landing at the target location.

All five functions are implemented as independent ROS 2 modules and integrated into one end-to-end simulation system.

---

## Approach

The project uses a fully simulation-based approach:

- **PX4 SITL** simulates the UAV autopilot.
- **Gazebo Harmonic** provides the 3D physics environment, including terrain, obstacles, and the UAV model.
- **ROS 2 Jazzy** connects all five modules through publish/subscribe topics.
- **QGroundControl** provides mission upload and telemetry monitoring.
- **BeiDou short message** is simulated using software to inject rescue coordinates into the system.

---

## System Overview Diagram

```
BeiDou emergency coordinate (simulated)
        ↓
beidou_short_message module
        ↓  /target/emergency_coordinate
qgc_control module (QGroundControl + MAVLink)
        ↓  /mission/waypoints
path_planning module
        ↓  /fmu/in/trajectory_setpoint
PX4 SITL (UAV autopilot)
        ↓
Gazebo Harmonic (3D simulation)
        ↓
target_detection_tracking module ─── camera feed
        ↓  /target/location
path_planning module (precision landing)
        ↓
Rescue complete
```

---

## Scope

This project covers the full system from coordinate reception to landing in simulation. Physical hardware integration is outside the current project scope but the architecture is designed to support future real-world deployment.
