# Linux Run Guide — Full BDS-SMC2 Stack on the Group's ROS Machine

Launch the whole rescue stack on one Ubuntu/ROS 2 machine: portal reader →
auto-sender → ROS node → Gazebo, with the dashboard watching the BDS link.
Everything is the same Python you already have — only `python3` and the serial
port name (`/dev/ttyUSB0`) differ from Windows.

## 0. One-time setup

```bash
sudo apt install python3-serial               # for the serial scripts
cd ~/uav-emergency-rescue-bds/ros2_ws
git pull
colcon build --packages-select interfaces beidou_short_message
source install/setup.bash
# copy your BDS-SMC2 python/ scripts + data/ onto this machine (or git clone your repo)
```

Find the ESP32 port (when plugged in):
```bash
ls /dev/ttyUSB*        # usually /dev/ttyUSB0
sudo usermod -a -G dialout $USER   # once, so you don't need sudo for serial (re-login after)
```

## 1. Launch the stack — one terminal each

**Terminal 1 — portal reader** (pulls received messages):
```bash
cd ~/BDS-SMC2          # wherever your python/ + data/ live
python3 python/portal_reader.py --poll 10
```

**Terminal 2 — auto-sender** (CSV → node).  Mock first to test, then real:
```bash
python3 python/auto_sender.py --mock                 # no hardware, simulate
# OR, with the ESP32 plugged in and command-mode firmware flashed:
python3 python/auto_sender.py --port /dev/ttyUSB0
```

**Terminal 3 — dashboard**:
```bash
python3 python/tx_dashboard.py            # live data
# OR for the self-contained demo:
python3 python/tx_dashboard.py --mock-portal     # reads the mock portal file
```
Open a browser on the machine to **http://localhost:8765**

**Terminal 4 — ROS node** (decodes → publishes the rescue trigger):
```bash
cd ~/uav-emergency-rescue-bds/ros2_ws
source install/setup.bash
ros2 run beidou_short_message beidou_publisher_node
```

**Terminal 5 — Gazebo + the group's mission stack** (their launch file):
```bash
cd ~/uav-emergency-rescue-bds/ros2_ws
source install/setup.bash
ros2 launch bringup full_rescue.launch.py      # (group's launch — name per their repo)
```

## 2. Verify the join

In another terminal, confirm the decoded coordinate is on the ROS graph:
```bash
source install/setup.bash
ros2 topic echo /target/emergency_coordinate --once
```
When this shows a coordinate, the group's mission modules (Obj 1–4) react and the
Gazebo drone flies to it. That coordinate came through YOUR BDS link.

## 3. The screen layout for the demo

One screen, two windows side by side:
- **Left:** the browser (your dashboard) — BDS link health, payload journey, bit-perfect
- **Right:** the Gazebo window — the drone flying to the survivor
- Joined live by the `/target/emergency_coordinate` ROS topic

## 4. Quick reference — what each piece does

| Terminal | Script | Role |
|---|---|---|
| 1 | portal_reader.py | satellite → portal → CSV (receive) |
| 2 | auto_sender.py | coordinates CSV → node (transmit), retry/recycle |
| 3 | tx_dashboard.py | live BDS link view (green/red) |
| 4 | beidou_publisher_node | decode → /target/emergency_coordinate |
| 5 | Gazebo launch | drone responds (Obj 1–4) |

## Notes
- Serial port: Windows `COM14` → Linux `/dev/ttyUSB0`.
- Command-mode firmware (serial TX parser, see DESIGN_auto_sender.md) must be
  flashed for `--port` real mode; `--mock` needs no hardware.
- Portal tokens: same `python/portal_config.json` (re-copy from the browser if expired).
