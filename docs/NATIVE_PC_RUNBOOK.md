# Native-PC Integration Runbook — Full 5-Module End-to-End

**Purpose:** run the complete UAV Emergency Rescue pipeline (all 5 modules) end-to-end on a
**native Ubuntu 24.04 machine with a real GPU**. The control + RTK tiers were verified on WSL; the
**perception tier (camera/depth + YOLO) must run here** because it needs hardware OpenGL.

Pipeline: **BeiDou distress coordinate → mission state machine → RRT\* path → PX4/Gazebo flight →
RTK positioning + target detection → RTK-gated precision landing.**

> Companion docs: `docs/PIPELINE_ARCHITECTURE.md` (toolchain + topic map),
> `interfaces/integration_contract.md` (module contracts + Reconciliation Log), `INTEGRATION_2DAY_PLAN.md`.

---

## 0. Hardware / OS prerequisites (READ FIRST)

| Requirement | Why | Check |
|---|---|---|
| **Native Ubuntu 24.04** (not WSL) | camera/depth sensors render in Gazebo and need **hardware OpenGL** | `glxinfo \| grep "OpenGL renderer"` must show the **real GPU**, NOT `llvmpipe` |
| **GPU (CUDA capable)** | YOLO inference | `nvidia-smi` lists the GPU |
| ~15 GB RAM, multi-core | PX4 + Gazebo + YOLO | — |

🔴 **If `glxinfo` shows `llvmpipe`, STOP** — fix GPU OpenGL first, or the camera/depth feed will be empty/too slow.

---

## 1. Software prerequisites (install once)

```bash
# ROS 2 Jazzy + Gazebo Harmonic + ros_gz  (per ROS docs)
sudo apt install ros-jazzy-desktop ros-jazzy-ros-gz

# PX4-Autopilot (built with the DEPTH model)
cd ~ && git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot && make px4_sitl gz_x500_depth      # builds PX4 + the RGB-D x500 model

# micro-XRCE-DDS Agent
cd ~ && git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent && mkdir build && cd build && cmake .. && make

# Perception Python deps (CUDA torch for the GPU)
pip install ultralytics torch            # cv_bridge/opencv NOT needed (numpy only)

# QGroundControl on the GCS host (this machine or another on the LAN)
```

Versioning note: PX4 here uses **instance namespacing** (`/px4_1/*`) and **versioned topics**
(`..._v1`). The launch is already configured for that (`px4_ns:=px4_1`); confirm in §5.

---

## 2. Get the project + build

```bash
git clone https://github.com/Tevin-Wills/uav-emergency-rescue-bds.git
cd uav-emergency-rescue-bds/ros2_ws
rosdep install --from-paths src --ignore-src -r -y      # resolves ROS deps
source /opt/ros/jazzy/setup.bash
colcon build                                            # expect 8 packages
source install/setup.bash
```
✅ Expect **8 packages built**. The YOLO model ships in the repo
(`target_detection_tracking/models/kitti_person_yolov8n_best.pt`) — no download needed.

---

## 3. Datum sanity check (one-time, no change expected)

The whole system shares one **datum (Zurich, 47.397971, 8.546164)**. It is already synced across
`bringup/config/datum.yaml`, `rtk_positioning/config/base_station.yaml`, the three
`rtk_positioning/config/level3_*.yaml`, and the RTK node default. **Do not change** unless relocating —
if you do, change all of them together.

---

## 4. Start the simulation backbone

From the repo root:
```bash
SIM_MODEL=gz_x500_depth ./scripts/launch_sim_24.sh
```
This starts **PX4 SITL (instance 1) + Gazebo Harmonic (RGB-D x500) + micro-XRCE-DDS Agent (UDP 8888)**.
Leave it running. Expect: `Simulation stack running … GCS UDP port : 18571`.

---

## 5. 🔴 CRITICAL topic confirmation (do every first run on a new model)

The `gz_x500_depth` model may name topics differently than the default. In a second terminal:

```bash
# Gazebo-side sensor topics
gz topic -l | grep -iE "navsat|image|depth"
# ROS 2 side (PX4 via agent) — confirm namespace + versioned local position
source /opt/ros/jazzy/setup.bash && source ~/uav-emergency-rescue-bds/ros2_ws/install/setup.bash
ros2 topic list | grep -E "/px4_1/fmu/out/vehicle_local_position"
```
Record three things:
1. **RGB camera gz topic** (e.g. `/world/default/model/x500_depth_0/.../image`) → you will pass it as `rgb_gz_topic:=…`.
2. **navsat gz topic** — if the model name is NOT `x500_1`, edit the navsat bridge line in
   `ros2_ws/src/rtk_positioning/launch/level3_resilient_rtk.launch.py` (and rebuild) to match.
3. **local position topic** — confirm it is `/px4_1/fmu/out/vehicle_local_position_v1` (matches the
   launch default). If the suffix/namespace differs, pass `px4_ns:=…` and/or adjust in bringup.

---

## 6. Connect QGroundControl

Open QGC on the GCS host and add a **UDP link to port 18571** (the GCS port from §4). Use QGC to
monitor telemetry and, for the flight, to **upload a `.plan` mission** (mission-mode flight; see §8).

---

## 7. Launch the integrated system (all 5 modules)

Second terminal (ROS 2 sourced):
```bash
ros2 launch bringup full_rescue.launch.py \
    use_rtk:=true \
    use_detection:=true \
    scenario:=compound_disaster \
    px4_ns:=px4_1 \
    rgb_gz_topic:=<ACTUAL RGB gz topic from §5.1>
```
Variants:
- `scenario:=total_failure` — worst-case RTK (no corrections).
- `use_detection:=false` — RTK + control only (no camera tier).
- Realistic offset base (optional): set `base_station.yaml` to an offset coord (≤50 km) and add
  `--ros-args` param `enable_baseline_error_model:=true` to the RTK chain (see §11).

---

## 8. Health checks — confirm every module is live

```bash
# Backbone in
ros2 topic echo /px4_1/fmu/out/vehicle_local_position_v1 --once   # xy_valid: true
ros2 topic echo /gz/navsat --once                                 # Zurich lat/lon
ros2 topic hz /camera/image_raw                                   # ~10-30 Hz (perception)
ros2 topic hz /depth_camera                                       # depth frames

# RTK
ros2 topic echo /uav/rtk_position --once     # Zurich (matches /gz/navsat)
ros2 topic echo /uav/rtk_status --once       # e.g. 3|RTK_FIXED|0.03xx
ros2 topic echo /rtk/mission_viability --once# LANDING_VIABLE / APPROACH_VIABLE / ...
ros2 topic echo /rtk/baseline_km --once      # base<->drone distance

# Pipeline
ros2 topic echo /target/emergency_coordinate --once  # Zurich-area distress point
ros2 topic echo /mission/status --once               # phase machine
ros2 topic echo /uav/telemetry --once                # phase + rtk quality
ros2 topic echo /target/detection --once             # true once a survivor is seen
ros2 topic echo /target/location --once              # px4_local_enu pose
ros2 topic echo /planner/path --once                 # RRT* path
```
**Mission flow to observe:** distress received → phases advance (`DISTRESS_RECEIVED → … → LANDING`);
detection fires during `IN_FLIGHT/TARGET_ACQUIRED/LANDING`; landing **holds** if RTK viability is poor
and **proceeds** when `LANDING_VIABLE` (or `ABORTED` on timeout).

**Fly it:** upload a `.plan` in QGC and start the mission (mission-mode). The drone flies; RTK +
detection run; the gate governs the precision landing.

---

## 9. 📁 WHERE DATA IS STORED (collect these after each run)

All under the repo `results/` tree unless noted. **Raw run artifacts are gitignored** (regenerated each
run); commit only curated outputs with `git add -f`.

| Data | Location | Format | Produced by |
|---|---|---|---|
| **RTK run log** (position, status, accuracy, viability, error) | `results/logs/rtk_positioning/level3/<prefix>_<timestamp>.csv` | CSV (timestamped, never overwritten) | `logger_node` |
| **Detection log** | `results/logs/target_detection_tracking/detections.jsonl` | JSONL | `target_detection_node` |
| **Detection screenshots** | `results/screenshots/target_detection_tracking/target_detection_<ns>.ppm` | PPM (every 10 s when a target is seen) | `target_detection_node` |
| **PX4 flight log (ULog)** | `~/PX4-Autopilot/build/px4_sitl_default/rootfs/log/<date>/*.ulg` | ULog | PX4 |
| **Run video / screenshots (manual)** | `results/videos/` , `results/screenshots/` | mp4 / png | operator |
| **Full topic recording (recommended)** | `results/bags/<run_name>/` | rosbag2 (`.db3`) | `ros2 bag record` (below) |

Record everything for the review:
```bash
mkdir -p results/bags
ros2 bag record -o results/bags/run_$(date +%Y%m%d_%H%M%S) \
  /uav/rtk_position /uav/rtk_status /rtk/mission_viability /rtk/baseline_km \
  /target/emergency_coordinate /mission/status /mission/waypoints /uav/telemetry \
  /target/detection /target/location /planner/path /map/obstacles
```

**How the data is used:** the RTK CSV → `results/graphs/rtk_positioning/analyse_level3.py` → report
figures; the detection JSONL + PPM are the perception evidence; the ULog cross-validates the flight;
the rosbag lets you replay/plot the whole mission offline.

---

## 10. Shutdown
`Ctrl+C` in the bringup terminal, then in the backbone terminal. Note **which RTK CSV is the valid run**
(timestamp) before analysing — multiple runs accumulate.

---

## 11. (Optional) Realistic offset RTK base station
The model defaults to a co-located base (baseline 0 = unchanged). For a realistic deployment:
1. Set `rtk_positioning/config/base_station.yaml` to a real location **within 50 km** of the operating area.
2. Launch the RTK chain with `enable_baseline_error_model:=true`.
Result: RTK accuracy grows with baseline (1 ppm) and the fix degrades FIXED→FLOAT→GNSS realistically.
Calibrate `rtk_baseline_ppm` / `baseline_*_km` / floor against RTKLIB or a real receiver (see
`PHASE3_RTKLIB_PLAN.md`).

---

## 12. Troubleshooting (known gotchas)

| Symptom | Cause | Fix |
|---|---|---|
| Gazebo slow / no camera frames | software OpenGL (`llvmpipe`) | use a real GPU (§0) |
| `/px4_1/fmu/*` topics empty | agent not running / wrong namespace | confirm agent on UDP 8888; check `px4_ns` |
| `vehicle_local_position` not found | versioned topic `_v1` / namespace | use `/px4_1/fmu/out/vehicle_local_position_v1` |
| `/uav/rtk_position` in wrong place | `base_station.yaml` ≠ datum | set base to the datum (§3) |
| No detection at all | `ultralytics/torch` missing; `require_local_pose` waiting; wrong RGB topic; mission phase not active | install deps; confirm `/px4_1/.../vehicle_local_position_v1`; set `rgb_gz_topic`; mission must be IN_FLIGHT/TARGET_ACQUIRED/LANDING |
| `/camera/image_raw` empty | wrong gz RGB topic | set `rgb_gz_topic:=<gz topic -l value>` |
| QGC won't connect | wrong UDP link | UDP **18571** to the sim host |

---

## 13. Success criteria (what a complete run looks like)
- All §8 topics live; `/uav/rtk_position` at the datum; detection publishes on a survivor.
- Mission walks the full phase sequence; the **landing gate reacts to real RTK viability**.
- Data captured in `results/` (CSV + JSONL + PPM + ULog + rosbag).
- A recorded video/screenshots of the run for the progress report.
