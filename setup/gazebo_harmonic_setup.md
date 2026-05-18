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

Simulation world files for this project are stored in:

```
simulation/worlds/
```

The main rescue scenario world file is:

```
simulation/worlds/earthquake_rescue_world.sdf
```

> This file is a placeholder. The full world will be developed during the simulation integration phase.

---

## Model Files

Custom Gazebo models for this project are stored in:

```
simulation/models/
```

Planned models:

| Model | Path |
|---|---|
| Survivor marker | `simulation/models/survivor_marker/` |
| Collapsed building | `simulation/models/collapsed_building/` |
| Obstacle blocks | `simulation/models/obstacle_blocks/` |
| Landing pad | `simulation/models/landing_pad/` |

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
