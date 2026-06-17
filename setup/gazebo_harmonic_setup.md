# Gazebo Harmonic Setup

## Overview

This project uses **Gazebo Harmonic**, which is the LTS version of Gazebo compatible with Ubuntu 24.04 and ROS 2 Jazzy.

> Do not use Gazebo Classic (gz-sim11 or earlier) — it is not supported with the PX4 + ROS 2 Jazzy stack.

---

## Installation

```bash
# Install Gazebo Harmonic
sudo apt update && sudo apt install gz-harmonic -y

# Install the ROS-Gazebo bridge for Jazzy
sudo apt install ros-jazzy-ros-gz -y
```

---

## Verify Installation

```bash
# Launch Gazebo GUI
gz sim

# Expected: Gazebo Harmonic window opens

# Check ROS-GZ bridge topics
source /opt/ros/jazzy/setup.bash
ros2 topic list  # After starting a simulation, /clock and /world/* topics should appear
```

---

## World Files

The canonical Gazebo world is **`worlds/rescue.sdf`** (custom post-disaster rescue scene on the
project's WGS-84 datum). See [`../docs/simulation_workflow.md`](../docs/simulation_workflow.md) for
details. Worlds reference their models via `model://` URIs resolved through Gazebo's resource path
(the repo root is on `GZ_SIM_RESOURCE_PATH`, so `model://<name>` → `models/<name>/`).

---

## Model Files

Gazebo models live in the top-level **`models/`** directory — textured mesh models used by
`worlds/rescue.sdf`:

```
models/
├── collapsed_house/  collapsed_fire_station/  collapsed_industrial/   # structures
├── person_standing/  person_walking/                                  # survivors
└── oak_tree/  pine_tree/  construction_barrel/                        # clutter / obstacles
```

---

## How Gazebo Connects to PX4

PX4 SITL uses Gazebo as its physics and rendering engine. The connection is handled automatically when PX4 is built with the Gazebo target:

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500
```

This starts both PX4 SITL and Gazebo Harmonic together.

---

## Notes

- On WSL2, Gazebo may have limited rendering performance. See [`wsl2_setup.md`](wsl2_setup.md).
- The ROS-GZ bridge (`ros_gz_bridge`) handles topic translation between ROS 2 and Gazebo.
