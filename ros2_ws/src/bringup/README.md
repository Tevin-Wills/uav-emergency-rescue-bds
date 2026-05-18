# bringup

**Type:** Shared package  
**Responsibility:** Full-system launch files for simulation and integration testing.

## Overview

This package contains launch files that start all modules together. It is the entry point for running the full UAV Emergency Rescue System.

## Structure

```
bringup/
├── package.xml
├── CMakeLists.txt
├── launch/
│   ├── full_system.launch.py       # Starts all modules
│   ├── simulation.launch.py        # Starts Gazebo + PX4 bridge only
│   └── integration_test.launch.py  # Starts selected modules for testing
└── README.md
```

## Usage

```bash
# Full system launch
ros2 launch bringup full_system.launch.py

# Simulation only
ros2 launch bringup simulation.launch.py
```

## TODO

- [ ] Implement `full_system.launch.py`
- [ ] Implement `simulation.launch.py`
- [ ] Add parameter passing between modules via launch arguments
- [ ] Add system-level health check on startup
