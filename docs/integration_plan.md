# Integration Plan

## Purpose

This document explains how the five independently developed modules will be combined into one working system for the final demonstration.

---

## Integration Strategy

Each team member develops and tests their module in isolation first. Integration is done incrementally — starting with the core communication backbone and adding modules one at a time.

### Integration Order

1. **Backbone first:** Confirm PX4 SITL + Gazebo Harmonic + micro-XRCE-DDS + ROS 2 Jazzy are all running together on the integration computer.
2. **Add `rtk_positioning`:** Verify `/uav/rtk_position` is published correctly.
3. **Add `beidou_short_message`:** Verify `/target/emergency_coordinate` is published.
4. **Add `qgc_control`:** Verify mission upload and `/mission/status` topic works end-to-end.
5. **Add `path_planning`:** Verify obstacle-free path is computed and trajectory setpoints sent to PX4.
6. **Add `target_detection_tracking`:** Verify target is detected in Gazebo and `/target/location` is published.
7. **Full system launch:** Run all modules together using `simulation/launch/full_rescue_sim.launch.py`.

---

## Integration Computer

Final integration will be performed on one main computer running native Ubuntu 24.04. This avoids WSL2 networking and rendering limitations during the demonstration.

**Recommended specs for the integration computer:**
- Ubuntu 24.04 LTS (native)
- 16 GB RAM minimum
- Discrete GPU (for Gazebo Harmonic rendering)
- Intel i7 or AMD Ryzen 7 equivalent

---

## Code Merge Process

Each student develops in their own feature branch:

```
feature/rtk-positioning
feature/qgc-control
feature/target-detection
feature/path-planning
feature/beidou-sms
```

Merge sequence:

1. Each student opens a pull request into the `dev` branch.
2. At least one other team member reviews the PR.
3. Merged code is tested on the integration computer.
4. When a stable milestone is confirmed, `dev` is merged into `main`.

---

## Required Common Standards

All modules must conform to the following before integration:

- Topic names as defined in [`interfaces/ros2_topics.md`](../interfaces/ros2_topics.md)
- Message formats as defined in [`interfaces/message_formats.md`](../interfaces/message_formats.md)
- Coordinate format as defined in [`interfaces/coordinate_format.md`](../interfaces/coordinate_format.md)
- Module inputs and outputs as defined in [`interfaces/integration_contract.md`](../interfaces/integration_contract.md)

---

## Final Demonstration Requirements

The final demonstration should show the following end-to-end sequence:

1. BeiDou short message received with rescue coordinates.
2. QGroundControl mission automatically updated.
3. UAV takes off from Gazebo world and follows planned path.
4. UAV avoids obstacles autonomously.
5. RTK positioning maintains accuracy throughout flight.
6. UAV detects and tracks the survivor marker in Gazebo.
7. UAV performs precision fixed-point landing at target.

Demonstration outputs expected:
- Gazebo simulation running live.
- QGroundControl showing UAV position and mission progress.
- ROS 2 topic printouts confirming message flow.
- Recorded video of the full run in `results/videos/`.

---

## Contingency Plan

If a module is not ready for final integration:

- The module can be stubbed: publish realistic test data on its required topics.
- This allows the rest of the system to demonstrate integration even if one module is incomplete.
- Stub data should be stored in `data/` and loaded by a simple Python publisher node.
