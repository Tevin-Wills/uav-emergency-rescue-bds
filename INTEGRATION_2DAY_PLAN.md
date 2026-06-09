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
2. ✅ **RTK L3 → mission wiring DONE** (2026-06-10). `mission_status_node` gates precision landing on
   `/rtk/mission_viability` (lands only on `LANDING_VIABLE`, else `LANDING_HOLD` → re-converge → land,
   or `ABORTED` on timeout); `/uav/rtk_status` informs the logs ("RTK_FLOAT, 0.80 m"). Permissive
   fallback when no viability (stubs-only). Verified hold→recover→COMPLETE, hold→timeout→ABORTED, and
   permissive regression. **Remaining:** run real `level3_resilient_rtk.launch.py` on the backbone so the
   viability is real (not simulated).
3. **target_detection deps** on the integration PC: `ultralytics`/`torch` + model file.
4. ✅ **RESOLVED — single datum/home = Zurich, shared parameter.** Decided 2026-06-10. Canonical datum
   in `bringup/config/datum.yaml` (47.3980, 8.5462 — matches RTK's validated `world_origin`), injected
   into every node via the bringup launch (`/**` wildcard). BeiDou distress coordinate is now *derived*
   from datum + offset (auto-consistent, lands in the QGC waypoint box). Hangzhou kept only as the
   narrative "target deployment region". Level 3 work untouched. (path_planning still plans in the local
   "map" frame for now; it reads the datum, ready for real-frame endpoints.)
5. **Deferred, tracked:** U1 — path_planning synthetic grid → live depth costmap (GitHub issue #1).
6. **Stage 2 — Foxglove ops view**, then **Stage 3 — custom dashboard** (see top of doc).

**Honest review fallback (unchanged):** if the backbone isn't ready, the demonstrable deliverable is the
complete control-plane topic-flow integration (all 5 nodes live, messages flowing, RRT\* avoiding
obstacles) even if the Gazebo flight is partial.

## Integration fix plan (from the file-by-file system audit, 2026-06-10)

A strict audit of every node's publishers/subscribers found the five modules build and the **control
plane flows**, but the system is **not yet a closed loop**. Five findings, prioritised below. P0–P2 are
doable headless and disturb no finished work; P3 needs the backbone + a decision.

### RTK level build-up (reference — so we never mix levels)
All three levels share `base_station_node` + `rtk_positioning_node` + `logger_node`. They differ on:
- **Ground-truth source:** L1 = `simulated_uav_node` (synthetic, NO Gazebo); L2/L3 = `px4_pose_adapter_node`
  ← `ros_gz_bridge` ← Gazebo (NEEDS backbone).
- **Corrections:** L1 = none (time-based status); L2 = `rtcm_correction_simulator_node` (nominal);
  L3 = `rtcm_correction_simulator_node` (disaster profile).
- **`/rtk/mission_viability`:** produced **only by L3**. ⇒ **Integration RTK = Level 3, and L3 requires the
  backbone.** There is no headless L3; do NOT invent hybrid chains (e.g. simulated_uav + L3 params).

### Status 2026-06-10
- **C1 (P0), C2 (P1), C3 (P2): DONE + verified** (headless). Details below.
- **C4 (P3): decided = uXRCE-DDS** (not MAVROS — see Reconciliation Log [C]); implementation deferred to
  the backbone; review fallback = PX4 mission mode via QGC (Windows, UDP 18571).
- **C5: DONE** — full toolchain + run architecture saved to `docs/PIPELINE_ARCHITECTURE.md`.
- **Two backbone configs:** `gz_x500` (GPS only → RTK + control + flight, runs on WSL headless) vs
  `gz_x500_depth` (+ camera/depth → target_detection, needs native GPU PC; WSL OpenGL is software
  `llvmpipe`). target_detection also needs `ultralytics`/`torch` installed + `require_local_pose` (PX4).
- **Run artifacts gitignored** (`results/logs/*.csv`, `results/screenshots/*.ppm`, `*.jsonl`).
- **NEXT ON RESUME:** one-time backbone bring-up check (RTK config) to confirm 🟡→🟢 (PX4+Gazebo
  headless + `/fmu/*` + `/gz/navsat`). Then validate C1/#2 against real RTK viability.

### P0 — Fix bringup RTK wiring  🔴 critical — ✅ DONE (C1)
**Problem:** `full_rescue.launch.py` launches the bare `rtk_positioning_node`, which has no inputs
(`/uav/ground_truth`, `/rtk/base_station`, `/rtk/simulated_rtcm` are produced by sibling nodes bringup
never launches) ⇒ `use_rtk:=true` produces nothing.
**Fix (launch wiring only, no level-mixing):** when `use_rtk:=true`, `IncludeLaunchDescription` of
`rtk_positioning/launch/level3_resilient_rtk.launch.py` (pass `scenario` arg) — the validated full L3 chain.
**Honest consequence:** L3 needs Gazebo, so real RTK output only appears **with the backbone up**; headless,
the chain starts but `px4_pose_adapter` has no `/gz/navsat` → no `/uav/rtk_position`. That is correct, not a
bug to paper over. The #2 landing-gate logic was already validated separately with an explicit
**simulated-viability unit test** (a test harness, NOT a fake RTK level).
**Files:** `bringup/launch/full_rescue.launch.py`. **Testable headless:** wiring yes; real data needs backbone.

### P1 — Route the planner to the real goal in a common frame  🔴 (GAP 2 + GAP 4)
`/target/location` and `/mission/waypoints` currently dead-end; `path_planning` plans to *parameterized*
local endpoints, ignoring the real rescue/target point. Fix: `path_planning_node` subscribes
`/mission/waypoints` (goal) + `/target/location` (landing re-target), converts RTK start + goal to the local
"map" frame via the shared datum (`obstacle_map.latlon_to_local`), and plans start→goal. Obstacles stay
synthetic until U1. **Files:** `path_planning_node.py`. **Testable headless:** ✅

### P2 — Publish `/uav/telemetry`  🟠 (GAP 5; quick win)
`mission_status_node` publishes `/uav/telemetry` (phase + last RTK status + viability) at 1 Hz to fulfil the
contract and feed the future dashboard. **Files:** `mission_status_node.py`. **Testable headless:** ✅

### P3 — Close the flight loop  🔴 (GAP 3; largest, gated)
Nothing commands the drone: `mission_status` is a state machine, `path_planning` doesn't feed PX4, Yvonne's
MAVROS `uav_control_node` is deferred. Resolve Reconciliation Log [C]: (a) uXRCE node converting
`/planner/path` → `/fmu/in/trajectory_setpoint`, or (b) MAVROS, or (demo fallback) PX4 **mission mode** via
QGC (no code). **Needs:** backbone + [C] decision. **Recommendation:** fallback for the review; schedule (a)
after. **Testable headless:** ❌

### Order
Commit #2 → **P0 → P1 → P2** (headless, low/medium risk) ⇒ coherent end-to-end control loop for the review.
**P3** + real L3-on-Gazebo validation wait for the backbone; mission-mode flight is the honest fallback.
