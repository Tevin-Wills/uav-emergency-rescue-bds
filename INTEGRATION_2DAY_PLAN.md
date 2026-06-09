# Two-Day System Integration Plan — UAV Emergency Rescue (BDS)

_Last updated: 2026-06-09. Owner: Student 1 (Tevin Wills). Status: execution started (Stage 1 integration). Dashboard added as 3-stage end goal._

## Goal
A live, end-to-end ROS 2 demo of the rescue pipeline:
**BeiDou coordinate → mission → flight in PX4/Gazebo → RTK positioning + target detection → precision landing**,
launched from one command, with topic flow visible.

**Why 2 days:** the next progress-report review + presentation must show the **system integration** as
the headline deliverable. The integrated, runnable pipeline (topics flowing end-to-end) is the minimum
we have to demonstrate at that review.

## End goal: a rescue operations dashboard (3-stage path)
On top of the integrated pipeline we are building an **operations view** that shows the live rescue
mission — *not* a QGroundControl replacement, but the rescue-specific story QGC cannot show
(BeiDou distress-coordinate ingestion → mission state machine → target detection → RTK fix quality →
precision landing). It is a faithful window into whatever the ROS 2 topic graph actually publishes, and
is honestly labeled as a **simulation / integration test harness**, not a fielded system. Sequencing is
strict — each stage is gated by the previous one being live:

1. **Stage 1 — Integration (this plan, Days 1–2).** Get the topic graph live end-to-end. A dashboard is
   pointless until topics actually publish. This is what the review must show.
2. **Stage 2 — Foxglove ops view (after Stage 1).** Stand up `foxglove_bridge` + Foxglove Studio panels
   (map from `NavSatFix`, `/mission/status` state machine, camera image, `/target/*`, RTK fix quality).
   Hours of work, zero frontend code — proves the pipeline visually for the demo.
3. **Stage 3 — Custom web dashboard (final path, time permitting).** Bespoke web app
   (`rosbridge_server` + `roslibjs` + map/video/plots) for polish and portfolio value. Built only after
   the topics are real and Foxglove has validated the data flow.

## ⚠️ Committed deferred upgrades (do NOT forget)

| # | Upgrade | Trigger / when | Status |
|---|---|---|---|
| U1 | **path_planning obstacle source: synthetic grid → live depth-camera costmap.** The salvaged RRT\* planner ships first with a static/synthetic `OccupancyGrid` (decoupled from the camera; target_detection untouched). Swap in a live `/depth_camera` → 2D costmap projection — same planner, only the grid source changes. path_planning + target_detection then share `/depth_camera`. | Once the PX4/Gazebo camera backbone is solid and validated | ⏳ Pending — tracked here + in planner node TODO + memory `project_pathplanning_upgrade` |

## Asset inventory (reality on `main` today)

| Module | State | Publishes | Consumes |
|---|---|---|---|
| `rtk_positioning` | ✅ Real | `/uav/rtk_position` (NavSatFix), `/uav/rtk_status`, `/uav/raw_gps`, `/rtk/*` | PX4 odom (L2/L3) |
| `target_detection_tracking` | ✅ Real (afiqhs) | `/target/detection` (Bool), `/target/location` (PoseStamped) | `/camera/image_raw`, `/depth_camera`, `/fmu/out/vehicle_local_position`, `/uav/rtk_position`, `/uav/rtk_status`, `/mission/status` |
| `px4_msgs` | ✅ Real | (msg defs) | — |
| `interfaces` | ✅ Builds | `SimulatedRtcm.msg`, **`EmergencyCoordinate.msg`** | — |
| `beidou_short_message` | ✅ **Real ROS 2** (`beidou_publisher_node`) | `/target/emergency_coordinate`, `/rescue/beidou_message` | — |
| `qgc_control` | ✅ **Built** — `mission_status_node` (stub) + Yvonne's MAVROS node (deferred) | `/mission/status`, `/mission/waypoints` | `/target/emergency_coordinate`, `/target/detection` |
| `path_planning` | ✅ **Real** — salvaged RRT\* on synthetic grid (`path_planning_node`) | `/planner/path`, `/map/obstacles` | `/mission/status`, `/target/emergency_coordinate`, `/uav/rtk_position` |
| `bringup` / `full_rescue_sim.launch.py` | ✅ **Done** — `full_rescue.launch.py` launches all 5; sim wrapper delegates to it | — | — |

**Status (2026-06-09):** all 5 modules are ROS 2 and build (8/8 pkgs). The **control-plane flows
end-to-end** (BeiDou → mission state machine → RRT\* path), verified via stubs-only smoke test.
**Critical-path dependency remaining:** the heavy real nodes (RTK L3, target_detection) need the
**PX4 SITL + Gazebo Harmonic + micro-XRCE-DDS + camera/depth backbone** — not yet stood up, still the
hardest part (Block A). target_detection's `/mission/status` input is now satisfied by `qgc_control`.

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

## Progress log — software glue COMPLETE (2026-06-09)
The original "first concrete tasks" are all done:
1. ✅ `EmergencyCoordinate.msg` added to `interfaces`.
2. ✅ `beidou_short_message`, `qgc_control`, `path_planning` are buildable ROS 2 packages.
3. ✅ BeiDou wrapper `beidou_publisher_node` publishes `/target/emergency_coordinate`.
4. ✅ `bringup/full_rescue.launch.py` launches all 5; sim wrapper delegates to it.
5. ✅ Contract reconciled — `/uav/rtk_position` → `NavSatFix` (+ Reconciliation Log [A][B][C]).
6. ✅ path_planning: ROS 1 RRT\* salvaged into ROS 2 (`rrt_star_planner` + synthetic grid); real avoidance verified.

## Revised next steps (what remains)
**Software glue is done; remaining work is backbone + decisions + the two deferred stages.**

1. **Block A — stand up the backbone** (still the #1 risk; owner: integration-PC holder + afiqhs):
   PX4 SITL + Gazebo Harmonic + micro-XRCE-DDS agent + camera/depth drone. Unlocks RTK L3 + target_detection.
2. **RTK = Level 3 (resilient)** is the integration level (not L2): run `level3_resilient_rtk.launch.py`
   on the backbone; wire `/uav/rtk_status` + `/rtk/mission_viability` into mission decisions.
3. **target_detection deps** on the integration PC: `ultralytics`/`torch` + model file.
4. **TEAM DECISION — single datum/home.** Modules are geographically inconsistent (BeiDou=Hangzhou,
   PX4/QGC=Zurich). Agree one origin so planner/RTK/mission share a frame; until then path_planning
   plans in a local "map" frame with parameterized endpoints.
5. **Deferred, tracked:** U1 — path_planning synthetic grid → live depth costmap (GitHub issue #1).
6. **Stage 2 — Foxglove ops view**, then **Stage 3 — custom dashboard** (see top of doc).

**Honest review fallback (unchanged):** if the backbone isn't ready, the demonstrable deliverable is the
complete control-plane topic-flow integration (all 5 nodes live, messages flowing, RRT\* avoiding
obstacles) even if the Gazebo flight is partial.
