# Environment Setup Summary

## Shared Baseline

All team members use the following standardized stack regardless of platform:

| Component | Version |
|-----------|---------|
| OS | Ubuntu 24.04 LTS (Noble Numbat) |
| ROS 2 | Jazzy Jalisco |
| Gazebo | Harmonic (LTS) |
| PX4 | v1.14+ or main branch |
| micro-XRCE-DDS Agent | v2.4.3 (build from source) |
| QGroundControl | Latest stable AppImage |

> **Important:** Use ROS 2 **Jazzy**, not Humble. Jazzy is the correct LTS distribution for Ubuntu 24.04. Humble targets Ubuntu 22.04.

> **Important:** Use micro-XRCE-DDS Agent **v2.4.3** specifically. v3.x silently breaks the PX4–ROS 2 bridge.

---

## Detailed Setup Guides

Full step-by-step instructions are in the `setup/` folder:

| Guide | Purpose |
|---|---|
| [`setup/ubuntu_24_04_native_setup.md`](../setup/ubuntu_24_04_native_setup.md) | Native Ubuntu 24.04 setup and build flow |
| [`setup/wsl2_setup.md`](../setup/wsl2_setup.md) | WSL2-specific notes, limitations, and workarounds |
| [`setup/ros2_jazzy_setup.md`](../setup/ros2_jazzy_setup.md) | ROS 2 Jazzy installation and workspace setup |
| [`setup/gazebo_harmonic_setup.md`](../setup/gazebo_harmonic_setup.md) | Gazebo Harmonic installation and world setup |
| [`setup/px4_setup.md`](../setup/px4_setup.md) | PX4 SITL clone, build, and ROS 2 bridge setup |
| [`setup/qgroundcontrol_setup.md`](../setup/qgroundcontrol_setup.md) | QGroundControl install and mission upload |

---

## Quick Start (Native Ubuntu)

```bash
# Source ROS 2 Jazzy
source /opt/ros/jazzy/setup.bash

# Clone the repository
git clone https://github.com/Tevin-Wills/uav-emergency-rescue-bds.git
cd uav-emergency-rescue-bds

# Build the ROS 2 workspace
cd ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

---

## Quick Start (WSL2)

For WSL2 users, follow the same steps as native Ubuntu. Additionally:

- Run QGroundControl on Windows (not in WSL2).
- If Gazebo GUI has issues, add to `~/.bashrc`:

```bash
export QT_QPA_PLATFORM=xcb
```

See [`setup/wsl2_setup.md`](../setup/wsl2_setup.md) for all WSL2-specific caveats.

---

## Native Ubuntu vs WSL2 Comparison

| Capability | Native Ubuntu | WSL2 |
|---|---|---|
| Full Gazebo simulation | Yes | Limited (WSLg) |
| GPU rendering | Yes | Partial |
| QGroundControl | Run locally | Run on Windows |
| ROS 2 build and test | Yes | Yes |
| Module development | Yes | Yes |
| Final integration demo | Recommended | Not recommended |

---

## Verifying the Stack

After setup, confirm everything works:

```bash
# ROS 2
source /opt/ros/jazzy/setup.bash
ros2 topic list

# Gazebo bridge (start simulation first)
ros2 topic echo /clock

# PX4 bridge (after starting MicroXRCEAgent)
ros2 topic list | grep fmu
```

---

## TODO

- [ ] Add exact PX4 parameter settings for RTK integration
- [ ] Document colcon build flags for individual packages
- [ ] Add troubleshooting section for common WSL2 errors
