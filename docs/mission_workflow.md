# Mission Workflow

## Overview

This document describes the end-to-end operational workflow for a UAV emergency rescue mission, from receiving distress coordinates to completing the rescue flight and landing.

---

## Mission Phases

### Phase 1 — Distress Signal Reception

1. A distress signal is received via the **BeiDou short message service**.
2. The `beidou_sms` module decodes the message and extracts GPS rescue coordinates.
3. Coordinates are published to `/beidou/rescue_coords`.

### Phase 2 — Mission Planning

1. `uav_control_gcs` receives the rescue coordinates.
2. An operator reviews and approves the mission in **QGroundControl**.
3. Mission waypoints are uploaded to PX4 via MAVLink.
4. Path planning computes an obstacle-free route to the target location.

### Phase 3 — Pre-Flight

1. RTK base station is active and transmitting RTCM corrections.
2. UAV acquires RTK fix — `rtk_positioning` confirms `/uav/rtk_status` is healthy.
3. PX4 runs pre-arm checks; system is armed via QGroundControl.

### Phase 4 — Flight Execution

1. UAV takes off and follows planned waypoints.
2. `path_planning_rescue` continuously monitors for obstacles and updates trajectory.
3. RTK positioning maintains centimetre-level accuracy throughout.
4. Telemetry (position, battery, status) is streamed back to QGroundControl.

### Phase 5 — Target Acquisition and Landing

1. `target_tracking_landing` activates camera-based detection near the rescue zone.
2. Target is detected, tracked, and followed.
3. UAV transitions to fixed-point landing mode over the target.
4. PX4 executes precision landing.

### Phase 6 — Post-Mission

1. UAV lands and disarms.
2. Mission log is saved.
3. Telemetry and data are reviewed via QGroundControl.

---

## State Machine (High Level)

```
IDLE
  │
  ▼
DISTRESS_RECEIVED  (BeiDou SMS)
  │
  ▼
MISSION_PLANNED    (QGC + path_planning)
  │
  ▼
PRE_FLIGHT_CHECK   (RTK fix confirmed, PX4 armed)
  │
  ▼
IN_FLIGHT          (waypoint following, obstacle avoidance)
  │
  ▼
TARGET_ACQUIRED    (target_tracking active)
  │
  ▼
LANDING            (fixed-point precision landing)
  │
  ▼
MISSION_COMPLETE
```

---

## TODO

- [ ] Define ROS2 state machine node in `bringup`
- [ ] Add timing diagrams per phase
- [ ] Document abort and return-to-home procedures
- [ ] Add simulation scenario scripts for each phase
