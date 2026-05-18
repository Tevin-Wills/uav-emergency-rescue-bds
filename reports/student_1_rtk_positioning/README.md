# Student 1 — RTK Positioning Report

## Assigned Objective

UAV RTK Positioning — configure a simulated RTK base-rover GNSS setup and integrate RTK corrections into PX4 to achieve centimetre-level UAV positioning accuracy.

## Personal Report Scope

- Background and motivation for high-precision GNSS positioning in UAV rescue.
- RTK GNSS system design: base station, rover, RTCM correction flow.
- PX4 integration: how RTCM corrections are fed into the flight controller.
- ROS 2 node design for `rtk_positioning`.
- Simulation setup and test results.
- Analysis of positioning accuracy (expected: ≤ 5 cm horizontal in RTK Fixed mode).
- Comparison with standard GPS accuracy.

## Expected Simulation Evidence

- RTK fix acquisition log showing transition from GPS_ONLY → RTK_FLOAT → RTK_FIXED.
- Position error graph over time (horizontal and vertical).
- ROS 2 topic echo screenshots for `/uav/rtk_position` and `/uav/rtk_status`.
- Gazebo UAV trajectory showing stable positioning.

## Expected Diagrams, Tables, Logs, Screenshots

- System architecture diagram for RTK base-rover setup.
- Table comparing GPS vs RTK positioning accuracy.
- GNSS log files in `results/logs/`.
- RTK error graphs in `results/graphs/`.
- Gazebo screenshots in `results/screenshots/`.

## Folder Structure

```
student_1_rtk_positioning/
├── README.md         ← this file
├── outline.md        ← report outline and chapter plan
├── figures/          ← diagrams, architecture figures
├── tables/           ← data tables
└── references/       ← bibliography and reference notes
```
