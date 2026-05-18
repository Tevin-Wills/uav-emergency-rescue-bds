# Simulation Worlds

This folder contains Gazebo Harmonic world files for the UAV emergency rescue simulation.

## Planned World File

**`earthquake_rescue_world.sdf`** — A post-earthquake disaster area world including:

- Uneven terrain representing rubble and debris.
- Collapsed building models from `simulation/models/collapsed_building/`.
- Obstacle blocks from `simulation/models/obstacle_blocks/` for path planning testing.
- A survivor marker from `simulation/models/survivor_marker/` as the rescue target.
- A landing pad from `simulation/models/landing_pad/` for precision landing.

## Status

World file is planned. Place the `.sdf` file in this folder when ready.

To launch the world with PX4 SITL, it will be called from `simulation/launch/full_rescue_sim.launch.py`.
