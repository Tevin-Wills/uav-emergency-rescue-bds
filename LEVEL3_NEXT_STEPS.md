# Level 3 — Next Steps and Remaining Tasks
**Last updated:** 2026-06-03  
**Project:** UAV Emergency Rescue BDS — RTK Positioning Module (Student 1, Tevin Wills)  
**Deadline:** Progress report due 2026-06-04

---

## Current Status Summary

| Item | Status |
|---|---|
| Level 1 — code, data, 5 graphs | Done ✓ |
| Level 2 — code, data, 6 graphs, ULog cross-validation | Done ✓ |
| Level 3 — all code (Steps 2.1–2.6) | Done ✓ |
| Level 3 — compound disaster CSV (drone hovering, invalid) | Exists — DO NOT USE FOR ANALYSIS |
| Level 3 — compound disaster CSV (drone flying, 878 s) | Done ✓ — `rtk_level3_compound_disaster_20260603_195803.csv` |
| Level 3 — total failure CSV (drone flying, 843 s) | Done ✓ — `rtk_level3_total_failure_20260603_201957.csv` |
| analyse_level3.py | **NEXT — write now** |
| 6 Level 3 figures | Not yet generated |

---

## Critical Decision Made

**Level 3 must have actual drone flight — not hover.**  
Level 2 flew a real 8-waypoint mission (170 m range, 166 s). Level 3 must match this.  
A flight mission has been designed: 5 waypoints, ~780 seconds, 5 m/s cruise speed.  
The old compound disaster CSV (drone hovering) is kept as a reference but must NOT be  
used in the final analysis.

---

## Step-by-Step Tasks

---

### STEP 1 — Enter Level 3 Mission in QGC **[DONE ✓]**

Open QGC → Plan view → clear any existing mission.

#### Mission settings
- **Takeoff altitude:** 50 m (relative)
- **Cruise speed:** add `DO_CHANGE_SPEED` command at the top, set **5 m/s**

#### Waypoints (enter in this exact order)

| # | Label | Latitude | Longitude | Altitude (relative) | Hold (s) |
|---|---|---|---|---|---|
| T | Takeoff | 47.397971 | 8.546164 | 50 m | — |
| 1 | Departure end | 47.401564 | 8.546164 | 50 m | 0 |
| 2 | Approach end | 47.404106 | 8.549926 | 50 m | 0 |
| 3 | Collapse site (search zone) | 47.405058 | 8.551335 | 50 m | **360** |
| 4 | Landing point | 47.403261 | 8.550670 | **20 m** | 30 |
| RTL | Return to Launch | — | — | — | — |

**Why 5 m/s:** The departure and approach legs are 400 m each. At 5 m/s cruise  
(~3.5–4.5 m/s effective with deceleration), each leg takes ~100–115 s, aligning  
with the 120-second phase windows in the signal profile.

**Phase alignment:**
- WP1 leg (departure): 0–120 s — open sky, ideal signal
- WP2 leg (approach): 120–240 s — signal beginning to degrade
- WP3 hold 360 s (search zone): 240–600 s — peak degradation, periodic gaps
- WP4 leg + hold (landing): 600–660 s — critical precision phase
- RTL (exit): 660–780 s — signal recovering on return

After entering all waypoints, **upload the mission to the vehicle** in QGC.  
The QGC estimated flight time should show approximately 12–14 minutes.

---

### STEP 2 — Run Compound Disaster Scenario (Run 2) **[DONE ✓]**

**Prerequisites before starting:**
- Terminal 1: `~/launch_sim_24.sh` is running (PX4 SITL + Gazebo + micro-XRCE-DDS Agent)
- QGC: connected, mission uploaded, drone shows Ready to Fly
- The old compound disaster CSV already in level3/ folder — this is fine, logger creates a new file

**Sequence (timing matters):**

```bash
# Terminal 1 (already running):
~/launch_sim_24.sh

# QGC:
# 1. Arm the drone
# 2. Switch to Mission mode — drone takes off and starts flying toward WP1
# 3. Watch the drone start moving toward WP1

# Terminal 2 — start IMMEDIATELY when drone begins moving toward WP1:
cd ~/uav-emergency-rescue-bds && ./run_level3.sh
```

**Confirm startup messages in Terminal 2:**
```
[rtcm_correction_simulator_node] Loaded 5 mission phases from .../level3_disaster_scenario.yaml
[rtcm_correction_simulator_node] RTCM correction simulator started — phase profile (Level 3)
[logger_node] writing to: .../level3/rtk_level3_compound_disaster_YYYYMMDD_HHMMSS.csv
```
The timestamp on the new CSV will be different from the old hovering CSV. This confirms it is a new run.

**Let it run for the full 780 seconds (~13 minutes).**  
Watch for signal degradation messages during search zone phase (240–600 s).

**Stop it:**  
Press Ctrl+C in Terminal 2 when the RTL phase is complete (~13–14 minutes after starting).

---

### STEP 3 — Verify Compound Disaster CSV **[DONE ✓]**

Run these commands immediately after stopping:

```bash
ls -lh ~/uav-emergency-rescue-bds/results/logs/rtk_positioning/level3/
wc -l ~/uav-emergency-rescue-bds/results/logs/rtk_positioning/level3/*.csv
head -2 ~/uav-emergency-rescue-bds/results/logs/rtk_positioning/level3/rtk_level3_compound_disaster_*NEW*.csv
tail -3 ~/uav-emergency-rescue-bds/results/logs/rtk_positioning/level3/rtk_level3_compound_disaster_*NEW*.csv
```

**What to check:**
- Two CSV files exist: old (163345) and new (new timestamp)
- New file has **~7,800 rows** (780 s × 10 Hz)
- Header ends with: `gnss_noise_std_m,mission_viability,scenario`
- `ground_truth_x` and `ground_truth_y` columns show values changing over time (drone was moving)
- Last column: `compound_disaster`

**Critical check — confirm drone actually moved:**
```bash
python3 -c "
import csv
rows = list(csv.DictReader(open('$(ls ~/uav-emergency-rescue-bds/results/logs/rtk_positioning/level3/rtk_level3_compound_disaster_*.csv | tail -1)')))
xs = [float(r['ground_truth_x']) for r in rows if r['ground_truth_x'].strip()]
print(f'X range: {min(xs):.1f} to {max(xs):.1f} m')
print(f'Max displacement: {max(abs(x) for x in xs):.1f} m')
"
```
Expected: X range spanning at least 100+ metres. If it shows near-zero throughout, the drone did not fly — do not proceed to Step 4, investigate first.

---

### STEP 4 — Run Total Failure Scenario (Run 3) **[DONE ✓]**

**Same mission, same waypoints — do NOT change QGC.**

Reset the drone first:
- In QGC: after RTL lands, disarm
- Switch to Mission mode again — drone will restart the mission from WP1

```bash
# Start run_level3.sh with total_failure when drone starts moving toward WP1:
cd ~/uav-emergency-rescue-bds && ./run_level3.sh total_failure
```

**Confirm startup:**
```
[rtcm_correction_simulator_node] RTCM correction simulator started — fixed schedule (Level 2)
[logger_node] writing to: .../level3/rtk_level3_total_failure_YYYYMMDD_HHMMSS.csv
```
Note: "fixed schedule (Level 2)" is correct — total failure uses fixed parameters, not a phase profile.

**Runtime:** The total failure scenario has fixed conditions (no phases). Run it for at least **5 minutes (300 seconds)** to collect enough data. You can stop earlier than 13 minutes — 300 s at 10 Hz = 3,000 rows, which is sufficient.

Press Ctrl+C after ~5 minutes.

---

### STEP 5 — Verify Total Failure CSV **[DONE ✓]**

```bash
wc -l ~/uav-emergency-rescue-bds/results/logs/rtk_positioning/level3/rtk_level3_total_failure_*.csv
head -2 ~/uav-emergency-rescue-bds/results/logs/rtk_positioning/level3/rtk_level3_total_failure_*.csv
```

**What to check:**
- At least 3,000 rows
- Header ends with `gnss_noise_std_m,mission_viability,scenario`
- Last column: `total_failure`
- `rtk_status_name` column: should be `GNSS_ONLY` throughout (no corrections)
- `ground_truth_x` and `ground_truth_y`: should vary (drone is moving)

---

### STEP 6 — Write analyse_level3.py **[CURRENT STEP]**

**Tell Claude Code:** "The two Level 3 CSVs are collected. Write analyse_level3.py."

Claude Code will write the script to:
`~/uav-emergency-rescue-bds/results/graphs/rtk_positioning/analyse_level3.py`

The script produces **6 figures** saved to `results/graphs/rtk_positioning/level3/`:

| Figure | Content |
|---|---|
| `l3_compound_scenario_profile.png` | GNSS noise + correction quality over mission time |
| `l3_error_over_time.png` | RTK error shaded by mission phase |
| `l3_uncertainty_over_time.png` | Dynamic uncertainty vs fixed Level 2 accuracy |
| `l3_viability_timeline.png` | Mission viability state over time |
| `l3_three_run_comparison.png` | Baseline vs compound disaster vs total failure |
| `l3_mission_phase_accuracy.png` | Box plot: approach phase vs landing phase accuracy |

---

### STEP 7 — Push to GitHub

```bash
cd ~/uav-emergency-rescue-bds
git add ros2_ws/src/rtk_positioning/ results/ run_level3.sh
git commit -m "Add Level 3 resilient RTK simulation — compound disaster + total failure runs + analysis"
git push
```

---

## Files and Their Purpose (Reference)

| File | Purpose |
|---|---|
| `config/level3_disaster_scenario.yaml` | Full scenario config with phase_profile (5 phases, 780 s) |
| `config/level3_disaster_scenario_params.yaml` | ROS2-safe scalar params only (no phase_profile list) |
| `config/level3_total_failure.yaml` | Total failure config (fixed GNSS_ONLY conditions) |
| `launch/level3_resilient_rtk.launch.py` | Launches all 6 Level 3 nodes |
| `run_level3.sh` | Wrapper — sources ROS2, checks DDS ports, calls launch file |
| `src/rtk_positioning/rtcm_correction_simulator_node.py` | Simulates disaster signal conditions over time |
| `src/rtk_positioning/rtk_positioning_node.py` | Applies corrections, outputs dynamic uncertainty + viability |
| `src/rtk_positioning/logger_node.py` | Writes CSV with all Level 3 columns |
| `results/logs/rtk_positioning/level3/` | All Level 3 CSVs (old hovering run + new flying runs) |
| `results/graphs/rtk_positioning/level3/` | Output folder for 6 figures (created by analyse_level3.py) |

---

## Key Rules — Do Not Break

- The old compound disaster CSV (`rtk_level3_compound_disaster_20260603_163345.csv`) must NOT be used in analysis. It was collected with the drone hovering, not flying.
- Level 1 and Level 2 must remain runnable — do not touch their configs or launch files.
- Both Level 3 runs (compound disaster and total failure) must use the same 5-waypoint QGC mission so trajectories are comparable.
- analyse_level3.py must explicitly pick the LATEST compound disaster CSV, not the old one.

---

## What to Say to Claude Code When You Return

Simply say: **"I am back. Let us continue with Level 3."**  
Claude Code will read this file and the memory, and pick up exactly where we left off.
