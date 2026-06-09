# UAV Emergency Rescue System Based on BeiDou Navigation and Short Message Communication

A five-member university engineering team project that builds a simulation-based integrated UAV emergency rescue system using PX4 SITL, ROS 2 Jazzy, Gazebo Harmonic, RTK GNSS positioning, and BeiDou short message communication.

---

## Project Description

This project demonstrates a complete UAV emergency rescue workflow in simulation:

1. A simulated BeiDou short message delivers rescue coordinates from a survivor.
2. The mission is planned and uploaded via QGroundControl.
3. The UAV flies an autonomous obstacle-free path to the target location.
4. RTK GNSS positioning provides centimetre-level accuracy throughout the flight.
5. The UAV detects and tracks the rescue target using an onboard camera.
6. The UAV performs a precision fixed-point landing at the target.

All five functions are implemented as independent ROS 2 modules and integrated into one end-to-end simulation system.

---

## System Overview

```
BeiDou short message (simulated)
        ↓
beidou_short_message → /target/emergency_coordinate
        ↓
qgc_control (QGroundControl + MAVLink)
        ↓  /mission/waypoints
path_planning
        ↓  /fmu/in/trajectory_setpoint
PX4 SITL ↔ Gazebo Harmonic
        ↓
rtk_positioning + target_detection_tracking
        ↓
Rescue complete — precision landing
```

---

## Team Modules

| Student | Package | Responsibility |
|--------|---------|----------------|
| Student 1 | `rtk_positioning` | RTK GNSS base-rover setup, centimetre-level position topics |
| Student 2 | `qgc_control` | QGroundControl mission upload, MAVLink telemetry, command flow |
| Student 3 | `target_detection_tracking` | Camera-based target detection, tracking, fixed-point landing |
| Student 4 | `path_planning` | Obstacle avoidance, autonomous route planning, trajectory to PX4 |
| Student 5 | `beidou_short_message` | BeiDou short message decode, rescue coordinate forwarding |

Shared packages: `interfaces` (custom ROS 2 message and service types), `bringup` (full-system launch files).

---

## Repository Structure

```
uav-emergency-rescue-bds/
├── README.md
├── .gitignore
│
├── docs/                          # Project-level documentation
│   ├── project_overview.md
│   ├── system_architecture.md
│   ├── team_roles.md
│   ├── simulation_workflow.md
│   ├── integration_plan.md
│   └── environment_setup.md
│
├── setup/                         # Installation guides
│   ├── ubuntu_24_04_native_setup.md
│   ├── wsl2_setup.md
│   ├── ros2_jazzy_setup.md
│   ├── gazebo_harmonic_setup.md
│   ├── px4_setup.md
│   └── qgroundcontrol_setup.md
│
├── interfaces/                    # Shared interface documentation
│   ├── message_formats.md
│   ├── ros2_topics.md
│   ├── coordinate_format.md
│   └── integration_contract.md
│
├── ros2_ws/src/                   # All ROS 2 packages
│   ├── rtk_positioning/
│   ├── qgc_control/
│   ├── target_detection_tracking/
│   ├── path_planning/
│   ├── beidou_short_message/
│   ├── interfaces/                # Shared .msg and .srv definitions
│   └── bringup/                   # Full-system launch files
│
├── simulation/                    # Gazebo worlds, models, and launch
│   ├── worlds/
│   ├── models/
│   └── launch/
│
├── missions/                      # QGroundControl .plan mission files
│
├── data/                          # Sample data for module testing
│
├── reports/                       # Individual student report folders
│   ├── student_1_rtk_positioning/
│   ├── student_2_qgc_control/
│   ├── student_3_target_detection/
│   ├── student_4_path_planning/
│   └── student_5_beidou_short_message/
│
└── results/                       # Simulation outputs
    ├── screenshots/
    ├── logs/
    ├── graphs/
    └── videos/
```

---

## Technology Stack

| Component | Version |
|-----------|---------|
| OS | Ubuntu 24.04 LTS |
| ROS 2 | Jazzy Jalisco |
| Gazebo | Harmonic (LTS) |
| PX4 | v1.14+ SITL |
| QGroundControl | Latest stable |
| Language | Python / C++ |
| Protocol | MAVLink |

---

## Development Environment

The team supports two environments:

- **Native Ubuntu 24.04** — recommended for full simulation and final integration.
- **WSL2 Ubuntu 24.04** — acceptable for individual module development and testing.

See [`docs/environment_setup.md`](docs/environment_setup.md) for a summary, and the `setup/` folder for detailed step-by-step guides.

---

## Basic Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/Tevin-Wills/uav-emergency-rescue-bds.git
cd uav-emergency-rescue-bds

# 2. Source ROS 2 Jazzy
source /opt/ros/jazzy/setup.bash

# 3. Install dependencies
cd ros2_ws
rosdep install --from-paths src --ignore-src -r -y

# 4. Build all ROS 2 packages
colcon build --symlink-install
source install/setup.bash
```

For PX4 SITL, Gazebo, and QGroundControl setup, see the `setup/` folder.

---

## Git Workflow

The team works on a **single `main` branch** — all modules live in one tree and are
integrated continuously. (The earlier `dev` integration branch was retired once work
consolidated onto `main`.)

```
main   ← single shared working + integration branch (all modules)
```

- Commit your module work directly to `main`, or use a short-lived branch and open a
  pull request into `main` for anything you want reviewed first.
- Pull (`git pull`) before you start and before you push, so you stay in sync.
- Keep each module inside its own package under `ros2_ws/src/` to avoid collisions.

---

## Access

This repository is **private** and intended only for the five team members. Do not share access without team agreement.
