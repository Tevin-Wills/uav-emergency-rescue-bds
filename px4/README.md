# PX4 Configuration

This directory contains PX4-specific configuration files and notes for the UAV Emergency Rescue System.

## Contents

- `configs/` — PX4 parameter files and airframe configurations

## PX4 Version

Use PX4 **v1.14+** or the `main` branch. This is the first version with stable Ubuntu 24.04 support.

```bash
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot
git checkout main
bash ./Tools/setup/ubuntu.sh
```

## SITL Simulation

Default simulation target for this project:

```bash
make px4_sitl gz_x500
```

For instance 1 (used with the team launch script, UDP port 18571):

```bash
PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL=x500 ./build/px4_sitl_default/bin/px4 -i 1
```

## micro-XRCE-DDS Bridge

Start the agent before launching any ROS2 nodes:

```bash
MicroXRCEAgent udp4 -p 8888
```

## Key Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `EKF2_GPS_CTRL` | 7 | Enable GPS fusion |
| `EKF2_HGT_REF` | 1 | Use GPS for height reference |
| `COM_RC_IN_MODE` | 1 | Joystick disabled (offboard/GCS only) |

> Full parameter files will be added to `configs/` as each module matures.

## TODO

- [ ] Add RTK-specific PX4 parameter file
- [ ] Document airframe selection for simulation
- [ ] Add parameter backup/restore instructions
