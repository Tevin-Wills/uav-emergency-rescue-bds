# QGroundControl Setup

## Overview

QGroundControl (QGC) is the ground control station used to upload waypoint missions, arm the UAV, and monitor telemetry during simulation and real flight.

---

## Installation

### Native Ubuntu

Download the latest AppImage from the QGroundControl website:

```bash
# Download (replace URL with the latest release from qgroundcontrol.com)
wget https://d176tv9ibo4jno.cloudfront.net/latest/QGroundControl.AppImage -O ~/QGroundControl.AppImage
chmod +x ~/QGroundControl.AppImage
./QGroundControl.AppImage
```

### WSL2 Users

Install QGroundControl on Windows, not inside WSL2. Download the Windows installer from the QGroundControl website and run it normally.

---

## Connect to PX4 SITL

When PX4 SITL is running, QGroundControl connects automatically:

1. Start PX4 SITL — this project uses `scripts/launch_sim_24.sh`, which runs **PX4 instance 1**.
2. Start QGroundControl.
3. QGC detects PX4 over UDP and connects automatically.

> **Port note:** PX4 maps the GCS UDP port by instance — instance 0 (bare `make px4_sitl gz_x500`) uses **18570**, while **instance 1** (this project's `launch_sim_24.sh`, `-i 1`) uses **18571**. Point QGC at **18571** for the project's standard setup.

No manual configuration is required for the default SITL setup.

---

## Upload a Waypoint Mission

1. Open QGroundControl.
2. Click **Plan** in the top menu.
3. Click **File** → **Open** and select a `.plan` file from `missions/`.
4. Review the waypoints on the map.
5. Click **Upload** to send the mission to PX4.
6. Switch to **Fly** view and arm the vehicle.

---

## Monitor Telemetry

In the **Fly** view:

- Real-time vehicle position is shown on the map.
- Battery, altitude, speed, and mode are shown in the HUD.
- The **Analyze** menu provides MAVLink Inspector and Log Download tools.

---

## Mission Files

Planned mission files for this project are stored in:

```
missions/
├── qgc_search_mission.plan
├── emergency_target_mission.plan
└── fixed_point_landing.plan
```

> These are placeholders. Real `.plan` files will be created during the mission development phase.

---

## Notes

- QGC communicates with PX4 via MAVLink over UDP.
- On WSL2, QGC on Windows connects to PX4 in WSL2 over localhost — no extra routing needed.
- For telemetry data logging, use QGC's built-in log download feature after each flight.
