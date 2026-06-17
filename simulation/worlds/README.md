# Simulation Worlds

This folder contains Gazebo Harmonic world files for the UAV emergency rescue simulation.

## Active Gazebo Harmonic World

**`../gz_worlds/disaster_baylands.sdf`** — A Baylands-derived post-disaster rescue survey world including:

- Baylands terrain and water from the PX4 Gazebo world.
- Collapsed building and rubble primitives from `../gz_models/`.
- High-contrast simple survivor-person models for camera detection tests.
- A short survey mission in `../ros2_ws/src/path_planning/missions/disaster_baylands_survey.plan`.

The world is installed into PX4 as:

```text
~/Projects/PX4-Autopilot/Tools/simulation/gz/worlds/disaster_baylands.sdf
```

Launch it with:

```bash
cd ~/Projects/PX4-Autopilot
PX4_GZ_WORLD=disaster_baylands make px4_sitl gz_x500_depthlight
```

The older `simulation/models/*` folders are still useful placeholders for higher-fidelity future assets.
