# Mission Files

This folder stores QGroundControl and PX4 mission plan files (`.plan` format) for the UAV emergency rescue simulation.

## Planned Mission Files

### `qgc_search_mission.plan`

An area search pattern mission that covers the disaster zone in a grid or lawnmower pattern. Used for initial survey when the exact survivor location is not yet known.

### `emergency_target_mission.plan`

A direct-flight mission to the BeiDou rescue coordinate. The UAV flies from its starting position directly to the target location received via BeiDou short message.

### `fixed_point_landing.plan`

A precision approach and landing sequence. The UAV descends and performs a fixed-point landing at the target coordinate, guided by the `target_detection_tracking` module.

---

## How to Use

1. Open QGroundControl.
2. Go to **Plan** view.
3. Click **File** → **Open** and select a `.plan` file from this folder.
4. Review waypoints on the map.
5. Click **Upload** to send the mission to PX4 SITL.

---

## Status

Mission files are planned. They will be created using QGroundControl during the mission development phase and saved here.
