# interfaces

**Type:** Shared package  
**Responsibility:** Custom ROS2 message and service definitions shared across all modules.

## Overview

All custom message and service types used by more than one package are defined here. This avoids circular dependencies and keeps type definitions in one place.

## Structure

```
interfaces/
├── package.xml
├── CMakeLists.txt
├── msg/    # Custom message definitions (.msg files)
├── srv/    # Custom service definitions (.srv files)
└── README.md
```

## Planned Types

### Messages (`msg/`)

| Name | Fields | Used By |
|------|--------|---------|
| `RescueCoords.msg` | `float64 latitude`, `float64 longitude`, `float64 altitude`, `string source` | `beidou_sms` → `uav_control_gcs`, `path_planning_rescue` |
| `MissionWaypoint.msg` | TBD | `uav_control_gcs` → `path_planning_rescue` |

### Services (`srv/`)

| Name | Purpose |
|------|---------|
| `StartMission.srv` | Trigger mission start from bringup |
| `AbortMission.srv` | Emergency abort across all modules |

## TODO

- [ ] Define `RescueCoords.msg`
- [ ] Define `MissionWaypoint.msg`
- [ ] Define service types with team
- [ ] Add `package.xml` and `CMakeLists.txt` with correct message generation setup
