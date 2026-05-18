# Native Ubuntu 24.04 Setup

## Overview

Native Ubuntu 24.04 is the recommended development environment for this project. It provides full GPU access for Gazebo Harmonic rendering, no networking limitations, and the best simulation performance.

---

## When to Use Native Ubuntu

- Full PX4 SITL + Gazebo Harmonic simulation.
- Final integration testing across all five modules.
- Any work that requires reliable GPU rendering or low-latency networking.

---

## Dependency Checklist

Before installing project-specific tools, confirm the following are available:

```bash
# Verify OS version
lsb_release -a
# Expected: Ubuntu 24.04 LTS (Noble Numbat)

# Verify internet access
ping -c 2 google.com

# Verify git
git --version
```

Required packages:

- `git`
- `curl`
- `python3` / `python3-pip`
- `build-essential`
- `cmake`

Install all at once:

```bash
sudo apt update && sudo apt install -y git curl python3 python3-pip build-essential cmake
```

---

## Project-Specific Setup

Follow each setup guide in this order:

1. [`ros2_jazzy_setup.md`](ros2_jazzy_setup.md) — Install ROS 2 Jazzy
2. [`gazebo_harmonic_setup.md`](gazebo_harmonic_setup.md) — Install Gazebo Harmonic
3. [`px4_setup.md`](px4_setup.md) — Clone and build PX4 SITL
4. [`qgroundcontrol_setup.md`](qgroundcontrol_setup.md) — Install QGroundControl

---

## Build and Run

After the full environment is installed:

```bash
# Clone the repository
git clone https://github.com/Tevin-Wills/uav-emergency-rescue-bds.git
cd uav-emergency-rescue-bds

# Source ROS 2
source /opt/ros/jazzy/setup.bash

# Build the ROS 2 workspace
cd ros2_ws && colcon build --symlink-install
source install/setup.bash
```

---

## Notes

- Always source ROS 2 before building or running nodes.
- For Gazebo + PX4 simulation, see [`px4_setup.md`](px4_setup.md).
- For the full integrated simulation launch, see `simulation/launch/full_rescue_sim.launch.py` once it is implemented.
