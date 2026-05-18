# Development Environment

## Shared Baseline

All team members use the following standardized stack regardless of platform:

| Component | Version |
|-----------|---------|
| OS | Ubuntu 24.04 LTS (Noble Numbat) |
| ROS2 | Humble Hawksbill |
| Gazebo | Harmonic (LTS) |
| PX4 | v1.14+ or main branch |
| micro-XRCE-DDS Agent | v2.4.3 (build from source) |
| QGroundControl | Latest stable AppImage |

> **Important:** Use micro-XRCE-DDS Agent **v2.4.3** specifically. v3.x silently breaks the PX4-ROS2 bridge.

---

## Native Ubuntu 24.04

### Installation Flow

```bash
# 1. Install ROS2 Humble
sudo apt update && sudo apt install software-properties-common curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2.list'
sudo apt update && sudo apt install ros-humble-desktop -y
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

# 2. Install Gazebo Harmonic + ROS-GZ bridge
sudo apt install ros-humble-ros-gz -y

# 3. Clone and build PX4
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot && bash ./Tools/setup/ubuntu.sh
make px4_sitl gz_x500

# 4. Build micro-XRCE-DDS Agent v2.4.3
git clone -b v2.4.3 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent && mkdir build && cd build
cmake .. && make -j$(nproc) && sudo make install

# 5. Install QGroundControl
chmod +x QGroundControl.AppImage
./QGroundControl.AppImage
```

### Build Flow

```bash
cd ~/uav-emergency-rescue-bds
source /opt/ros/humble/setup.bash
cd ros2_ws && colcon build --symlink-install
source install/setup.bash
```

### Running PX4 + Gazebo Simulation

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500
```

In a second terminal:

```bash
MicroXRCEAgent udp4 -p 8888
```

---

## WSL2 Ubuntu 24.04

### Additional Setup Notes

WSL2 requires a few extra steps compared to native Ubuntu.

**QGroundControl (run on Windows side):**
QGroundControl should be installed and run on Windows, not inside WSL2. It connects to PX4 running in WSL2 via UDP.

- Default UDP port: `18571` (PX4 instance 1)
- No extra configuration needed — WSL2 bridges UDP to Windows automatically.

**Gazebo GUI (WSLg):**
Ubuntu 24.04 on WSL2 uses WSLg for GUI apps. If Gazebo shows a black screen, force X11 rendering:

```bash
export QT_QPA_PLATFORM=xcb
```

Add it to `~/.bashrc` to make it permanent.

**GPU Rendering:**
WSL2 does not fully expose GPU hardware to Gazebo in all configurations. If rendering is slow or broken, fall back to software rendering:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
```

> Note: Software rendering is slow but stable. For best results, use native Ubuntu with a dedicated GPU.

**Known WSL2 Caveats:**
- 3D rendering performance is limited by WSLg architecture, not the Ubuntu version.
- QGC on Windows communicates with PX4 in WSL2 over localhost UDP — this generally works out of the box.
- If WSL2 networking causes issues, check that `wsl --version` shows WSL 2 (not WSL 1).

### Launch Script

The team lead maintains a launch script at `~/launch_sim_24.sh` that starts PX4 + Gazebo and the micro-XRCE-DDS Agent together for WSL2 use:

```bash
bash ~/launch_sim_24.sh
```

Source ROS2 in a separate terminal after launch:

```bash
source /opt/ros/humble/setup.bash
source ~/uav-emergency-rescue-bds/ros2_ws/install/setup.bash
```

---

## Verifying the Stack

Run these checks after setup to confirm everything is working:

```bash
# ROS2
ros2 topic list

# Gazebo bridge
ros2 topic echo /clock

# PX4 bridge (after starting MicroXRCEAgent)
ros2 topic list | grep px4
```

---

## TODO

- [ ] Add exact PX4 parameter settings for RTK integration
- [ ] Document colcon build flags for individual packages
- [ ] Add troubleshooting section for common WSL2 errors
