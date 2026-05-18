# UAV Emergency Rescue System

A five-member university engineering team project integrating high-precision UAV positioning, autonomous mission control, target detection and tracking, path planning, and BeiDou short message communication into a unified emergency rescue platform.

---

## System Overview

The system combines the following technologies into a single end-to-end rescue workflow:

- **PX4 Autopilot** — flight controller firmware and SITL simulation
- **ROS2 Humble** — middleware for inter-module communication
- **Gazebo Harmonic** — 3D simulation environment
- **RTK GNSS** — centimetre-level positioning (rover + base station)
- **QGroundControl** — ground control station for mission upload and telemetry
- **BeiDou Short Message Service** — satellite-based rescue coordinate communication

---

## Team Modules

| Member | Package | Responsibility |
|--------|---------|----------------|
| Member 1 | `rtk_positioning` | RTK GNSS base-rover setup, high-precision pose topics |
| Member 2 | `uav_control_gcs` | QGroundControl mission upload, telemetry, command flow |
| Member 3 | `target_tracking_landing` | Camera-based detection, tracking, fixed-point landing |
| Member 4 | `path_planning_rescue` | Obstacle avoidance, autonomous route planning |
| Member 5 | `beidou_sms` | BeiDou short message send/receive, coordinate forwarding |

Shared packages: `interfaces` (common message/service definitions), `bringup` (full-system launch files).

---

## Repository Structure

```
uav-emergency-rescue-bds/
├── README.md
├── .gitignore
├── docs/                        # Architecture, workflows, environment guides
├── px4/                         # PX4 configuration files
├── ros2_ws/src/                 # All ROS2 packages
│   ├── rtk_positioning/
│   ├── uav_control_gcs/
│   ├── target_tracking_landing/
│   ├── path_planning_rescue/
│   ├── beidou_sms/
│   ├── interfaces/
│   └── bringup/
├── simulation/                  # Gazebo worlds, models, launch, configs
├── config/                      # RTK, QGC, and BeiDou config files
├── scripts/                     # Setup, build, and run scripts
└── .github/workflows/           # CI pipeline
```

---

## Development Environment

The team uses a standardized stack across all machines:

- **OS:** Ubuntu 24.04 LTS (native or WSL2)
- **ROS2:** Humble Hawksbill
- **Gazebo:** Harmonic (LTS)
- **PX4:** v1.14+ / main branch
- **QGroundControl:** Latest stable AppImage

See [`docs/dev_environment.md`](docs/dev_environment.md) for full setup instructions for both native Ubuntu and WSL2.

---

## Basic Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/Tevin-Wills/uav-emergency-rescue-bds.git
cd uav-emergency-rescue-bds

# 2. Set up the development environment
./scripts/setup_px4.sh

# 3. Build all ROS2 packages
./scripts/build_ros2.sh

# 4. Launch the full simulation
./scripts/run_simulation.sh

# 5. Run the full integrated system
./scripts/run_full_system.sh
```

---

## Git Workflow

```
main        ← stable milestones and final integration only
  └── dev   ← working integration branch
        ├── feature/rtk-positioning
        ├── feature/uav-control-gcs
        ├── feature/target-tracking
        ├── feature/path-planning
        └── feature/beidou-sms
```

- Work in your dedicated feature branch.
- Open a pull request into `dev` when a module milestone is ready.
- Merge from `dev` into `main` only at tested integration milestones.

---

## Access

This repository is **private** and intended only for the five team members. Do not share access without team agreement.
