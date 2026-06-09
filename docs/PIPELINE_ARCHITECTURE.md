# UAV Emergency Rescue — Pipeline Architecture

_Canonical reference for the system toolchain and how the five modules connect.
Last updated 2026-06-10._

## 1. Tool roster (who does what, runs where)

| Tool | Role | Runs where | Project config |
|---|---|---|---|
| **ROS 2 Jazzy** | Middleware all nodes speak | WSL | — |
| **Gazebo Harmonic** (`gz sim` 8.11) | Physics + world + sensors (drone, GPS, camera, depth) | WSL | model `x500_1`, world `default`, `HEADLESS=1` |
| **PX4 SITL** | Autopilot / flight control | WSL | `PX4_SIM_MODEL=gz_x500`, instance `-i 1` (MAV_SYS_ID 2) |
| **micro-XRCE-DDS Agent** | Bridges PX4 ⇄ ROS 2 (`/fmu/*` via `px4_msgs`) | WSL | `udp4 -p 8888` |
| **ros_gz_bridge** | Bridges Gazebo sensors → ROS 2 | WSL | navsat→`/gz/navsat`; camera/depth to add |
| **QGroundControl** | GCS: monitor + upload `.plan` + mission-mode flight | **Windows** | MAVLink over **UDP 18571** |
| **ultralytics + torch** | YOLOv8 inference for detection | WSL (GPU avail.) | ⚠️ not installed yet |
| **px4_msgs** | ROS 2 message defs for `/fmu/*` | WSL (built) | — |

## 2. Layered architecture

```
LAYER 5: OPERATOR (Windows)   QGroundControl ── MAVLink/UDP 18571 ──► PX4 SITL
LAYER 4: ROS 2 APP (WSL)      beidou → mission_status → path_planning → [flight_node C4]
                                  ↑          ↑   ↑                          │
                            rtk_positioning  │   target_detection           │
                                  │ /gz/navsat│ cam/depth │ /fmu/out/*       │ /fmu/in/*
LAYER 3: BRIDGES (WSL)        ros_gz_bridge ◄─ Gazebo   |   micro-XRCE-DDS Agent (UDP 8888)
LAYER 2: AUTOPILOT            PX4 SITL (x500_1) ◄────────┘
LAYER 1: SIMULATION          Gazebo Harmonic — dynamics + GPS + (camera/depth)
```

## 3. Connection / port map

| From → To | Protocol / port | Carries |
|---|---|---|
| PX4 SITL ⇄ Gazebo | gz transport (internal) | physics, sensor sim |
| PX4 SITL → XRCE Agent | uXRCE-DDS, **UDP 8888** | uORB ↔ DDS |
| XRCE Agent ⇄ ROS 2 | DDS | `/fmu/out/*` (state), `/fmu/in/*` (commands) |
| Gazebo → ros_gz_bridge → ROS 2 | gz transport → DDS | `/gz/navsat`, `/camera/image_raw`, `/depth_camera` |
| PX4 SITL ⇄ QGC (Windows) | MAVLink, **UDP 18571** | telemetry, mission upload |

## 4. Module ↔ tool/topic attachment

| Module | Consumes | Produces |
|---|---|---|
| **rtk_positioning** (L3 chain) | `/gz/navsat` (ros_gz) | `/uav/rtk_position`, `/uav/rtk_status`, `/rtk/mission_viability` |
| **beidou** | distress msg / datum | `/target/emergency_coordinate`, `/rescue/beidou_message` |
| **mission_status** | emergency_coord, `/target/detection`, RTK status+viability | `/mission/status`, `/mission/waypoints`, `/uav/telemetry` |
| **path_planning** | `/uav/rtk_position`, `/mission/waypoints`, `/target/location` | `/planner/path`, `/map/obstacles` |
| **target_detection** | `/camera/image_raw`+`/depth_camera` (ros_gz), `/fmu/out/vehicle_local_position` (XRCE), RTK, `/mission/status` | `/target/detection`, `/target/location` |
| **flight_node** (C4, uXRCE) | `/planner/path` | `/fmu/in/trajectory_setpoint` + `OffboardControlMode` + `/fmu/in/vehicle_command` → PX4 |
| **QGC** (Windows) | MAVLink state | `.plan` upload (mission-mode fallback) |

## 5. PX4 bridge decision (Reconciliation Log [C], resolved 2026-06-10)

**Standardise on PX4 / uXRCE-DDS (`px4_msgs`), NOT MAVROS.** Evidence: PX4 SITL built,
micro-XRCE-DDS Agent installed, `px4_msgs` built, Gazebo Harmonic + ros_gz in use, and
`target_detection` already consumes `/fmu/*`. MAVROS is **not installed** and used by only
one node (Yvonne's `uav_control_node`), which is therefore **retired from the integration
path or ported to uXRCE** (a conversation to have with its owner).
- **C4 real closed loop:** a uXRCE flight node `/planner/path → /fmu/in/trajectory_setpoint`
  (offboard) so the RRT* path actually steers the drone. Needs the backbone; post-review.
- **Review/demo fallback:** PX4 **mission mode** — upload a `.plan` via QGC, PX4 flies it,
  modules run alongside. No flight-node code; rides the same uXRCE stack.

## 6. Two backbone configurations (IMPORTANT)

`launch_sim_24.sh` currently uses `gz_x500` (**GPS only, NO camera/depth**). So:

| Config | Sim model | Bridges | Enables | Runs on |
|---|---|---|---|---|
| **RTK config** | `gz_x500` | navsat | rtk_positioning + control plane + flight | WSL (headless, no GPU-GL needed) |
| **Full-perception** | `gz_x500_depth` | navsat + camera + depth | + target_detection | **native GPU PC** (camera rendering needs hardware OpenGL; WSL is `llvmpipe` software GL) |

## 7. Startup sequence

```
1. ./launch_sim_24.sh        → PX4 SITL + Gazebo (x500_1, headless) + micro-XRCE-DDS Agent (8888)
2. QGC (Windows)             → connect UDP 18571 (monitor / upload mission)
3. ros_gz_bridge             → navsat (+ camera/depth for full-perception)  [navsat is in the L3 launch]
4. ros2 launch bringup full_rescue.launch.py use_rtk:=true use_detection:=<true on native PC>
```

## 8. Where logs / data land, and how they are used

| Producer | Output | Location | Format | Use |
|---|---|---|---|---|
| rtk_positioning `logger_node` | run log | `results/logs/rtk_positioning/level3/<prefix>_<ts>.csv` | CSV | `results/graphs/rtk_positioning/analyse_level3.py` → figures/report |
| target_detection | detections | `results/logs/target_detection_tracking/detections.jsonl` | JSONL | detection metrics |
| target_detection | screenshots | `results/screenshots/target_detection_tracking/*.ppm` | PPM | visual proof |
| PX4 SITL | flight log | `~/PX4-Autopilot/build/.../rootfs/log/*.ulg` | ULog | flight cross-validation (`.ulg` gitignored) |
| beidou / mission_status / path_planning | none (topics only) | — | — | — |

**Policy:** raw run logs/screenshots are **gitignored** (regenerated each run). Only curated
outputs deliberately selected for the report are committed (`git add -f`).
