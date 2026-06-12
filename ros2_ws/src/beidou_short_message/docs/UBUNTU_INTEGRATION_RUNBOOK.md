# Ubuntu Integration Runbook — beidou_short_message

Step-by-step verification of the BeiDou node on the integration machine
(Ubuntu 24.04 + ROS 2). Run this BEFORE the joint session. Total time: ~2 minutes.

The node now decodes three message formats behind the unchanged interface:
ASCII (`LAT:..,LON:..`), 112-bit binary rescue payload, legacy 64-bit binary.
Topics, message types, QoS and default sim behaviour are identical to before.

---

## 0. Prerequisites (once per machine)

```bash
source /opt/ros/jazzy/setup.bash    # or the distro installed on the machine
cd ~/uav-emergency-rescue-bds/ros2_ws   # adjust to the workspace path
git pull
```

## 1. Build (your packages only)

```bash
colcon build --packages-select interfaces beidou_short_message
source install/setup.bash
```

Expected: `Finished <<< interfaces` and `Finished <<< beidou_short_message`, no stderr.

## 2. Automated check (recommended)

```bash
bash src/beidou_short_message/scripts/verify_integration.sh
```

Expected final line: `ALL CHECKS PASSED — ready for integration`.
If the script complains about `bad interpreter` or `\r`, fix Windows line
endings once with: `sed -i 's/\r$//' src/beidou_short_message/scripts/verify_integration.sh`

The script runs the three checks below — they can also be done manually.

## 3. Manual check A — default sim behaviour (what the group bringup expects)

```bash
ros2 run beidou_short_message beidou_publisher_node
```

Expected log:
```
[INFO] ... Derived distress coordinate from datum (47.39797,8.54616) + offset (E60m,N90m) -> $CCTXM,0,LAT:47.3988,LON:8.5471*XX
[INFO] ... Decoded distress coordinate: lat=47.3988..., lon=8.5470... (src 0)
```

In a second terminal:
```bash
source install/setup.bash
ros2 topic echo /target/emergency_coordinate --once
```

Expected: `latitude: 47.398...`, `longitude: 8.547...`, `source_id: '0'`.
This is byte-for-byte the pre-upgrade behaviour. Ctrl+C the node.

## 4. Manual check B — real 112-bit binary rescue message (T001)

```bash
ros2 run beidou_short_message beidou_publisher_node --ros-args \
  -p raw_message:='$CCTXM,0,BIN:1D35DB5605079637007200A00101*CS'
```

(Use single quotes — `$CCTXM` inside double quotes gets eaten by bash.)

Expected log:
```
[INFO] ... Decoded distress coordinate: lat=49.0068822, lon=8.4383287 (src 0)
[INFO] ... Rescue payload fields (not yet in EmergencyCoordinate.msg): alt=114.0m R=1.6m priority=P1 survivor_id=1
```

The second line is the talking point for extending EmergencyCoordinate.msg.

## 5. Full multi-survivor demo (optional, for the meeting)

All six lab rescue-report records as ready-to-use messages:

| ID | raw_message parameter value |
|----|-----------------------------|
| T001 (P1, R1.6m)  | `$CCTXM,0,BIN:1D35DB5605079637007200A00101*CS` |
| T002 (P2, R11.9m) | `$CCTXM,0,BIN:1D35E03E05079134007204A60202*CS` |
| T003 (P2, R4.6m)  | `$CCTXM,0,BIN:1D35E12B0507782B007201CC0203*CS` |
| T004 (P0, R1.6m)  | `$CCTXM,0,BIN:1D35E0C405077A43007200A00004*CS` |
| T005 (P0, R3.3m)  | `$CCTXM,0,BIN:1D35E401050768E10072014A0005*CS` |
| T006 (P2, R2.0m)  | `$CCTXM,0,BIN:1D35E41B050769FB007200C80206*CS` |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: interfaces` | interfaces pkg not built/sourced | `colcon build --packages-select interfaces` then re-source |
| `Package 'beidou_short_message' not found` | forgot to source | `source install/setup.bash` |
| echo prints nothing | started echo before node | node republishes every 2 s (latched) — wait 2 s |
| `Could not decode BeiDou message` | quoting ate the `$` | use single quotes around the raw_message value |
| build uses stale code | old non-symlink install | `rm -rf build/ install/ log/` for these pkgs and rebuild |
