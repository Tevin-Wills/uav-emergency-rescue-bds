# Student 2 — QGC Control Report

## Assigned Objective

UAV Control Using QGroundControl — upload waypoint missions, manage MAVLink telemetry, and coordinate command flow between the GCS, ROS 2, and PX4.

## Personal Report Scope

- Background on ground control station software and MAVLink protocol.
- QGroundControl system design: mission upload, telemetry monitoring, command flow.
- ROS 2 node design for `qgc_control`.
- Integration with BeiDou coordinate input and path planning output.
- Simulation setup and test results.

## Expected Simulation Evidence

- QGroundControl screenshot showing successful mission upload to PX4 SITL.
- Telemetry data stream screenshots.
- ROS 2 topic echo for `/mission/status` and `/mission/waypoints`.
- Mission plan files in `missions/`.

## Folder Structure

```
student_2_qgc_control/
├── README.md
├── outline.md
├── figures/
├── tables/
└── references/
```
