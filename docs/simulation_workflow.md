# Simulation Workflow

## Overview

This document describes how simulation is structured for this project — from individual module testing through to the full integrated rescue mission simulation.

---

## Simulation Stack

| Tool | Role |
|---|---|
| PX4 SITL | UAV autopilot firmware (Software-In-The-Loop) |
| Gazebo Harmonic | 3D physics and rendering environment |
| micro-XRCE-DDS Agent | Bridge between PX4 and ROS 2 |
| ROS 2 Jazzy | Module communication middleware |
| QGroundControl | Mission upload and telemetry monitoring |

---

## Phase 1 — Individual Module Simulation

Each team member develops and tests their module in isolation first. This can be done on any machine (native Ubuntu or WSL2).

| Module | What to simulate independently |
|---|---|
| `rtk_positioning` | Simulate GNSS fix and RTCM correction; verify RTK topics are published |
| `qgc_control` | Connect QGC to PX4 SITL; upload a test mission; verify telemetry |
| `target_detection_tracking` | Feed a test image or video; verify target detection topics |
| `path_planning` | Feed test waypoints and obstacle map; verify trajectory output |
| `beidou_short_message` | Inject a test message; verify decoded coordinate is published |

Each student can use stub publishers to simulate the outputs of modules they depend on. Sample stub data is in `data/`.

---

## Phase 2 — Common Interface Testing

Before full integration, verify that shared interfaces are compatible:

1. Confirm all topic names match [`interfaces/ros2_topics.md`](../interfaces/ros2_topics.md).
2. Confirm all message formats match [`interfaces/message_formats.md`](../interfaces/message_formats.md).
3. Confirm coordinate format matches [`interfaces/coordinate_format.md`](../interfaces/coordinate_format.md).

Run two modules together and confirm that messages flow correctly between them before adding a third.

---

## Phase 3 — Full Integrated Simulation

The final integrated simulation runs all five modules together on one computer (native Ubuntu 24.04 recommended).

The main launch file will be:

```
simulation/launch/full_rescue_sim.launch.py
```

> This file is a placeholder. It will be implemented during the integration phase.

The expected sequence for the full simulation:

1. Start PX4 SITL + Gazebo Harmonic.
2. Start micro-XRCE-DDS Agent.
3. Source ROS 2 and the workspace.
4. Launch all five modules using `full_rescue_sim.launch.py`.
5. Open QGroundControl.
6. Inject a simulated BeiDou short message.
7. Observe the full rescue mission execute end-to-end.

---

## Native Ubuntu vs WSL2 Development

| Workflow | Native Ubuntu | WSL2 |
|---|---|---|
| Individual module dev | Yes | Yes |
| PX4 SITL only | Yes | Yes |
| Full Gazebo simulation | Yes | Limited |
| Final integration | Yes (recommended) | Not recommended |

Team members on WSL2 should develop their module in isolation and test it individually. The final integration run should happen on the designated integration computer (native Ubuntu).

---

## Simulation World

The rescue scenario world file is:

```
simulation/worlds/earthquake_rescue_world.sdf
```

This world includes:
- Terrain representing a post-earthquake disaster area.
- `simulation/models/collapsed_building/` — building rubble obstacles.
- `simulation/models/obstacle_blocks/` — additional obstacles for path planning.
- `simulation/models/survivor_marker/` — target that `target_detection_tracking` must detect.
- `simulation/models/landing_pad/` — precision landing target zone.

> World and model files are placeholders. They will be populated during the simulation development phase.

---

## Mission Files

QGroundControl mission files for the simulation are in `missions/`:

```
missions/
├── qgc_search_mission.plan       — area search pattern
├── emergency_target_mission.plan — fly to BeiDou rescue coordinate
└── fixed_point_landing.plan      — precision landing sequence
```

---

## TODO

- [ ] Implement `simulation/launch/full_rescue_sim.launch.py`
- [ ] Create `simulation/worlds/earthquake_rescue_world.sdf`
- [ ] Create Gazebo model files for all four models
- [ ] Add timing diagrams per mission phase
- [ ] Document abort and return-to-home procedures
