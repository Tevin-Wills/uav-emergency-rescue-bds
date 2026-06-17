# Simulation Workflow

## Overview

This document describes how simulation is structured for this project — from individual
module testing through to the full integrated rescue mission simulation. For the
authoritative toolchain and topic/port map see [`PIPELINE_ARCHITECTURE.md`](PIPELINE_ARCHITECTURE.md);
for the step-by-step end-to-end run see [`NATIVE_PC_RUNBOOK.md`](NATIVE_PC_RUNBOOK.md).

---

## Simulation Stack

| Tool | Role |
|---|---|
| PX4 SITL | UAV autopilot firmware (Software-In-The-Loop) |
| Gazebo Harmonic | 3D physics and rendering environment |
| micro-XRCE-DDS Agent | Bridge between PX4 and ROS 2 (`/fmu/*` via `px4_msgs`) |
| ros_gz_bridge | Bridges Gazebo sensors (navsat, camera, depth) → ROS 2 |
| ROS 2 Jazzy | Module communication middleware |
| QGroundControl | Mission upload and telemetry monitoring (runs on Windows for WSL users) |

Two backbone configurations are used (see `PIPELINE_ARCHITECTURE.md` §6):

| Config | Sim model | Enables | Runs on |
|---|---|---|---|
| **RTK / control** | `gz_x500` (GPS only) | rtk_positioning + control + flight | WSL (headless) or native |
| **Full perception** | `gz_x500_depth` (+ camera/depth) | + target_detection_tracking | native GPU PC (hardware OpenGL) |

---

## Phase 1 — Individual Module Simulation

Each team member develops and tests their module in isolation first. This can be done on
any machine (native Ubuntu or WSL2).

| Module | What to simulate independently |
|---|---|
| `rtk_positioning` | Simulate GNSS fix and RTCM correction; verify RTK topics are published |
| `qgc_control` | Connect QGC to PX4 SITL; upload a test mission; verify telemetry |
| `target_detection_tracking` | Feed a test image or video; verify target detection topics |
| `path_planning` | Feed test waypoints and obstacle map; verify trajectory output |
| `beidou_short_message` | Inject a test message; verify decoded coordinate is published |

Each student can use stub publishers to simulate the outputs of modules they depend on —
a simple Python node publishing realistic data on the required topics (topic and message
definitions are in `interfaces/`).

---

## Phase 2 — Common Interface Testing

Before full integration, verify that shared interfaces are compatible:

1. Confirm all topic names match [`interfaces/ros2_topics.md`](../interfaces/ros2_topics.md).
2. Confirm all message formats match [`interfaces/message_formats.md`](../interfaces/message_formats.md).
3. Confirm coordinate format matches [`interfaces/coordinate_format.md`](../interfaces/coordinate_format.md).
4. Confirm module contracts match [`interfaces/integration_contract.md`](../interfaces/integration_contract.md).

Run two modules together and confirm that messages flow correctly between them before
adding a third.

---

## Phase 3 — Full Integrated Simulation

The integrated simulation runs all five modules together. The control + RTK tiers run on
WSL; the perception tier needs a native GPU PC (see `NATIVE_PC_RUNBOOK.md`).

**Startup sequence:**

1. Start the backbone — PX4 SITL + Gazebo Harmonic + micro-XRCE-DDS Agent:
   ```bash
   ./scripts/launch_sim_24.sh                 # RTK/control (gz_x500)
   SIM_MODEL=gz_x500_depth ./scripts/launch_sim_24.sh   # full perception
   ```
2. Connect QGroundControl (UDP 18571) to monitor telemetry and upload a `.plan` mission.
3. Launch the five-module ROS 2 graph:
   ```bash
   ros2 launch bringup full_rescue.launch.py use_rtk:=true use_detection:=<true on GPU PC>
   ```
   A thin convenience wrapper also exists, run by file path (`simulation` is not a ROS 2 package):
   `ros2 launch simulation/launch/full_rescue_sim.launch.py` (delegates to `bringup/full_rescue.launch.py`).
4. Inject a simulated BeiDou short message and observe the rescue mission execute end-to-end.

See `NATIVE_PC_RUNBOOK.md` §5–§8 for the per-topic health checks and the mission flow to observe.

---

## Native Ubuntu vs WSL2 Development

| Workflow | Native Ubuntu | WSL2 |
|---|---|---|
| Individual module dev | Yes | Yes |
| PX4 SITL only | Yes | Yes |
| RTK / control tier | Yes | Yes (headless) |
| Full perception (camera/depth + YOLO) | Yes | No (needs hardware OpenGL) |
| Final integration demo | Yes (recommended) | Control/RTK only |

---

## Simulation World and Models

The current integrated runs use the **default Gazebo world** with the PX4 `x500` /
`x500_depth` model. A bespoke disaster world and custom Gazebo models are scoped under
`simulation/` but **not yet built** — those folders currently hold README stubs describing
the intended assets:

- `simulation/worlds/` — planned `earthquake_rescue_world.sdf` (post-earthquake terrain).
- `simulation/models/collapsed_building/` — building rubble obstacles.
- `simulation/models/obstacle_blocks/` — additional obstacles for path planning.
- `simulation/models/survivor_marker/` — target for `target_detection_tracking`.
- `simulation/models/landing_pad/` — precision landing target zone.

---

## Mission Files

QGroundControl mission `.plan` files live in `missions/`. The flight itself is currently
run in **PX4 mission mode** — a `.plan` is uploaded via QGC and PX4 executes it while the
ROS 2 modules run alongside. The specific search / target / landing `.plan` files are
created in QGC during mission development and saved to `missions/` (see `missions/README.md`).
