# ROS 2 Jazzy Setup

## Important

This project uses **ROS 2 Jazzy Jalisco**, which is the correct distribution for Ubuntu 24.04 LTS.

> Do not install ROS 2 Humble on Ubuntu 24.04. Humble targets Ubuntu 22.04. Jazzy is the LTS release for Ubuntu 24.04.

---

## Installation

```bash
# 1. Set locale
sudo apt update && sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2. Add the ROS 2 apt repository
sudo apt install software-properties-common curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2.list'

# 3. Install ROS 2 Jazzy desktop
sudo apt update && sudo apt install ros-jazzy-desktop -y

# 4. Install colcon and rosdep
sudo apt install python3-colcon-common-extensions python3-rosdep -y
sudo rosdep init
rosdep update
```

---

## Workspace Setup

```bash
# Source ROS 2 in every terminal session
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc

# Navigate to the project workspace
cd ~/uav-emergency-rescue-bds/ros2_ws

# Install dependencies
rosdep install --from-paths src --ignore-src -r -y

# Build
colcon build --symlink-install

# Source the workspace
source install/setup.bash
```

---

## Verification

```bash
# Check ROS 2 version
ros2 --version

# List available topics (should show /rosout after sourcing)
ros2 topic list

# Run a quick node test
ros2 run demo_nodes_py talker &
ros2 run demo_nodes_py listener
```

---

## Notes

- Source `/opt/ros/jazzy/setup.bash` before every new terminal session.
- After building the workspace, also source `ros2_ws/install/setup.bash`.
- The micro-XRCE-DDS Agent is required for PX4 ↔ ROS 2 communication. See [`px4_setup.md`](px4_setup.md).
