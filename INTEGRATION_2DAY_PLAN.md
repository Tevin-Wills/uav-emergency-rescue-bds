# Two-Day System Integration Plan — UAV Emergency Rescue (BDS)

_Last updated: 2026-06-09. Owner: Student 1 (Tevin Wills). Status: planning complete, execution not started._

## Goal
A live, end-to-end ROS 2 demo of the rescue pipeline:
**BeiDou coordinate → mission → flight in PX4/Gazebo → RTK positioning + target detection → precision landing**,
launched from one command, with topic flow visible.

## Asset inventory (reality on `main` today)

| Module | State | Publishes | Consumes |
|---|---|---|---|
| `rtk_positioning` | ✅ Real | `/uav/rtk_position` (NavSatFix), `/uav/rtk_status`, `/uav/raw_gps`, `/rtk/*` | PX4 odom (L2/L3) |
| `target_detection_tracking` | ✅ Real (afiqhs) | `/target/detection` (Bool), `/target/location` (PoseStamped) | `/camera/image_raw`, `/depth_camera`, `/fmu/out/vehicle_local_position`, `/uav/rtk_position`, `/uav/rtk_status`, `/mission/status` |
| `px4_msgs` | ✅ Real | (msg defs) | — |
| `interfaces` | ✅ Builds | only `SimulatedRtcm.msg` | — |
| `beidou_short_message` | ⚠️ Code only, NOT ROS 2 | (should: `/target/emergency_coordinate`, `/rescue/beidou_message`) | — |
| `qgc_control` | ❌ Empty stub | (should: `/mission/status`, `/mission/waypoints`, `/uav/telemetry`) | `/target/emergency_coordinate`, `/uav/rtk_position` |
| `path_planning` | ❌ Empty stub | (should: `/planner/path`, `/fmu/in/trajectory_setpoint`) | everything |
| `bringup` / `full_rescue_sim.launch.py` | ❌ Empty | — | — |

**Critical-path dependency:** `target_detection` (real) needs `/mission/status` (from `qgc_control`, empty)
and a camera-equipped drone in Gazebo publishing `/camera/image_raw` + `/depth_camera`. That backbone is
the hardest part — start it first.

## Strategy: real anchors + thin stubs (sanctioned by `docs/integration_plan.md` contingency clause)
Keep the two real nodes (RTK, target_detection). Fill the three gaps (qgc_control, path_planning, beidou)
with thin ROS 2 stub nodes that publish the contracted topics with realistic data. Yields a genuine,
demonstrable integrated topic graph within the time available.

## Day 1 — Backbone, build, contracts

**Block A — Backbone up (½ day, highest risk):**
- Native-Ubuntu integration machine: PX4 SITL + Gazebo Harmonic + micro-XRCE-DDS agent + ROS 2 Jazzy all talking.
- Confirm PX4↔ROS 2 bridge topics (`/fmu/out/vehicle_local_position`, `/fmu/out/vehicle_odometry`).
- Stand up camera + depth sensor on the Gazebo drone so `/camera/image_raw` and `/depth_camera` exist
  (afiqhs's `target_detection_sim.launch.py` is the reference). Owner: integration-PC holder + afiqhs.

**Block B — Everything builds (parallel):**
- `colcon build` the whole `ros2_ws`. Make the three stubs minimal buildable packages (`package.xml` + `setup.py`).
- Fix `rosdep` / YOLOv8 (torch) / `ros_gz_bridge` deps.
- Add the few custom `.msg` types still "TBD" to `interfaces/` (e.g. `EmergencyCoordinate`, `MissionStatus`),
  or agree to reuse `std_msgs`/`geometry_msgs` to save time.

**Block C — Lock the contract to reality:**
- Update `interfaces/integration_contract.md` + `ros2_topics.md`: `/uav/rtk_position` is **`NavSatFix`**
  (both RTK and target_detection already use it). Removes the only live type-mismatch.

## Day 2 — Glue, launch, rehearse

**Block D — Thin nodes (parallel by owner):**
- `beidou_short_message` (Maile/S1): wrap existing decode script in an rclpy node → publish
  `/target/emergency_coordinate` at startup (+ `/rescue/beidou_message`).
- `qgc_control` (S2 / stub): publish `/mission/status` phase sequence
  (`IDLE→DISTRESS_RECEIVED→MISSION_PLANNED→IN_FLIGHT→TARGET_ACQUIRED→LANDING→COMPLETE`) and `/mission/waypoints`;
  ideally upload a real `.plan` to PX4 so the drone actually flies.
- `path_planning` (S4 / stub): consume coordinate + RTK, publish `/planner/path` and feed PX4 trajectory
  (or rely on PX4 mission mode for the demo).

**Block E — `bringup` (S1):**
- Implement `ros2_ws/src/bringup/launch/full_rescue.launch.py` launching all five module nodes;
  make `simulation/launch/full_rescue_sim.launch.py` call it. Document external prereqs (PX4, agent, QGC).

**Block F — Dry run + capture:**
- Full launch; verify topic chain with `ros2 topic echo`. Record run to `results/videos/`,
  screenshots to `results/screenshots/`. Write a one-page integration result note.

## Ownership (team task; you are Student 1)
- **S1 (you/Claude):** RTK (done), `interfaces` msgs, `bringup` launch, BeiDou ROS 2 wrapper, integration glue/verification.
- **afiqhs (S3):** camera/depth in Gazebo + target_detection tuning.
- **S2:** `qgc_control` mission/status (real or stub).
- **S4:** `path_planning` (real or stub).
- **Maile (S5):** BeiDou decode hand-off for the wrapper.

## Top risks
1. Backbone + camera in Gazebo is the schedule-killer — start Block A first, parallel to everything.
2. Absent teammates for qgc_control/path_planning → fall back to stubs (already planned).
3. YOLOv8/torch + `ros_gz_bridge` deps on the integration PC — resolve during Block B.
4. Two days is tight for a fully-flying demo — honest fallback is a complete topic-flow integration
   (all nodes live, messages flowing) even if the Gazebo flight is partial.

## First concrete tasks when resuming (S1-owned, can start immediately)
1. Add custom `.msg` types to `ros2_ws/src/interfaces/msg/` (or decide to reuse std/geometry msgs).
2. Make `beidou_short_message`, `qgc_control`, `path_planning` minimal buildable packages.
3. BeiDou ROS 2 wrapper node publishing `/target/emergency_coordinate`.
4. `bringup` full-system launch skeleton.
5. Contract edit: `/uav/rtk_position` → `NavSatFix`.
