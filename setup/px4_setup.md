# PX4 SITL Setup

## Overview

PX4 is the autopilot firmware used in this project. It is run in Software-In-The-Loop (SITL) mode with Gazebo Harmonic as the physics simulator.

---

## Clone and Build PX4

```bash
# Clone PX4 with all submodules
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot

# Run the Ubuntu setup script (installs all PX4 dependencies)
bash ./Tools/setup/ubuntu.sh

# Build PX4 SITL with Gazebo Harmonic and the x500 quadrotor model
make px4_sitl gz_x500
```

> The first build takes 10–20 minutes.

---

## Run the Simulation

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500
```

This starts PX4 SITL and launches Gazebo Harmonic with the x500 model. The PX4 console will appear in the terminal.

---

## Connect ROS 2 to PX4

PX4 communicates with ROS 2 through the micro-XRCE-DDS bridge.

### Step 1: Install micro-XRCE-DDS Agent

```bash
# Build micro-XRCE-DDS Agent v2.4.3 (do not use v3.x — it breaks the PX4-ROS 2 bridge)
git clone -b v2.4.3 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent
mkdir build && cd build
cmake .. && make -j$(nproc) && sudo make install
```

### Step 2: Start the Agent

In a second terminal after PX4 is running:

```bash
MicroXRCEAgent udp4 -p 8888
```

### Step 3: Verify the Bridge

In a third terminal:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list | grep px4
```

You should see PX4 topics such as `/fmu/out/vehicle_odometry`.

---

## Connect QGroundControl

QGroundControl connects to PX4 SITL over UDP automatically:

- Default port: `18570` (MAVLink)
- On native Ubuntu: run QGC on the same machine.
- On WSL2: run QGC on Windows and it connects over localhost UDP.

See [`qgroundcontrol_setup.md`](qgroundcontrol_setup.md) for details.

---

## Notes

- PX4 build artifacts are gitignored. Do not commit the `PX4-Autopilot/` folder.
- The x500 model is a standard quadrotor suitable for testing all five project modules.
- For RTK integration parameters, see `ros2_ws/src/rtk_positioning/docs/`.
