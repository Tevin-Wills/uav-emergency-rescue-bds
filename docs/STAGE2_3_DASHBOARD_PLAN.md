# Stage 2 (Foxglove) & Stage 3 (Custom Dashboard) — Build & Run Plan

The rescue **operations view** sits on top of the integrated topic graph. It is a faithful
window into whatever the ROS 2 topics publish — a **simulation/integration ops view that
complements QGroundControl** (it shows the rescue-specific story QGC can't: BeiDou ingestion →
mission state → RTK fix quality → detection → RTK-gated landing). Two stages, strict sequencing:
**Stage 2 (Foxglove) proves the visualisation fast and key-free; Stage 3 (custom web app) is the
polished, portfolio-grade build, done only after Stage 2 validates the data flow.**

Prerequisite for either: the integrated system is running and topics are live (per
`docs/NATIVE_PC_RUNBOOK.md`). Stage 2 works for the **RTK/control tier on WSL now**; the camera
panel needs the GPU-PC perception tier.

---

## Stage 2 — Foxglove ops view (hours, zero frontend code)

**What it is:** Foxglove Studio (a free ROS 2 visualiser) connects to a `foxglove_bridge` running
inside ROS 2 over a WebSocket and renders configurable panels. No code — just panels + a layout.

### Install
```bash
sudo apt install ros-jazzy-foxglove-bridge
# Foxglove Studio: desktop app from foxglove.dev, or the web app at app.foxglove.dev
```

### Run
```bash
# Terminal: with the integrated system already running (bringup + backbone)
source /opt/ros/jazzy/setup.bash
ros2 launch foxglove_bridge foxglove_bridge_launch.xml          # serves ws://<host>:8765
# In Foxglove Studio: "Open connection" -> Foxglove WebSocket -> ws://localhost:8765
```

### Panels → topics (the "Rescue Ops" layout)
| Panel | Topic(s) | Shows |
|---|---|---|
| **Map** | `/uav/rtk_position` (NavSatFix), `/target/emergency_coordinate` | drone + distress location on a map |
| **State / Indicator** | `/mission/status`, `/uav/telemetry` | current mission phase + aggregated status |
| **Indicator (color)** | `/rtk/mission_viability`, `/uav/rtk_status` | RTK fix quality / landing viability (green/amber/red) |
| **Plot** | `/rtk/baseline_km`, `/rtk/accuracy` | baseline + accuracy over time |
| **3D** | `/planner/path` (Path), `/map/obstacles` (OccupancyGrid), `/target/location` (PoseStamped) | planned route, obstacles, survivor |
| **Image** | `/camera/image_raw` | live camera *(GPU-PC perception tier only)* |
| **Raw Messages / Log** | `/rescue/beidou_message`, `/target/detection` | decoded distress text, detection flag |

### Deliverable
Build the layout once, then **export it as a `.json`** (Foxglove → layout → export) and commit it
to the repo (suggested: `viz/foxglove_rescue_ops.json`) so any teammate loads the same ops view.
Capture screenshots/screen-recording of the live layout for the report/presentation.

---

## Stage 3 — Custom web dashboard (days; portfolio-grade)

**What it is:** a bespoke browser dashboard that subscribes to the ROS 2 topics and renders the
rescue mission. Best when you want a branded, embeddable, no-install operator view.

### Architecture
```
ROS 2 topics ──► rosbridge_server (WebSocket :9090) ──► roslib.js ──► browser DOM (map/gauges/feed)
/camera/image_raw ──► web_video_server (MJPEG :8080) ──► <img> tag
```

### Install
```bash
sudo apt install ros-jazzy-rosbridge-suite ros-jazzy-web-video-server
```

### Run (alongside the integrated system)
```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml     # ws://<host>:9090
ros2 run web_video_server web_video_server                      # http://<host>:8080 (MJPEG)
# serve the static dashboard:
python3 -m http.server 8000 --directory web/dashboard           # then open http://<host>:8000
```

### Frontend components (HTML/JS + `roslib.js`, or a small React app)
| Component | Source topic / feed | Implementation |
|---|---|---|
| Connection | `ws://host:9090` | `new ROSLIB.Ros({url})` |
| Map (Leaflet/Mapbox) | `/uav/rtk_position`, `/target/emergency_coordinate`, `/target/location`, `/planner/path` | plot markers + polyline |
| Mission phase banner | `/mission/status` | text/stepper |
| Telemetry feed | `/uav/telemetry` | scrolling text |
| RTK quality gauge | `/uav/rtk_status` (parse `code|name|σ`), `/rtk/mission_viability` | colour gauge (green/amber/red) |
| Baseline readout | `/rtk/baseline_km` | numeric/plot |
| Camera view | `/camera/image_raw` | `<img src="http://host:8080/stream?topic=/camera/image_raw">` |
| Detection indicator | `/target/detection` | LED/badge |

### Build steps
1. Scaffold `web/dashboard/` (`index.html`, `app.js`, `style.css`); pull `roslib.js` (CDN or npm).
2. Connect to rosbridge; create one `ROSLIB.Topic` subscriber per topic above; update the DOM on each message.
3. Map via Leaflet (lat/lon from NavSatFix); path as a polyline; gauges from RTK status/viability.
4. Camera via `web_video_server` MJPEG `<img>`.
5. Serve statically (http.server/nginx); open on the LAN.

### Scope / honesty
Position it as the **rescue-mission ops view** that *complements* QGC (QGC already shows raw
flight telemetry; this shows the BeiDou→detection→RTK→landing pipeline). Label it a simulation/
integration ops view, not a fielded GCS.

### Sequencing & effort
- Do Stage 3 **only after** Stage 2 has proven the data flow and the topic list is final.
- Reuse the same topic set as the Foxglove layout.
- Effort: ~2–4 focused days (frontend). The `infographic-builder` / `slides` skills can help
  prototype the visual layout quickly.
- Suggested repo home: `web/dashboard/` (static), or a `rosbridge`-launch helper in `bringup/`.

---

## Where each runs
| | RTK/control tier (WSL, now) | Full incl. camera (GPU PC) |
|---|---|---|
| Foxglove (Stage 2) | ✅ all panels except Image | ✅ all panels |
| Custom dashboard (Stage 3) | ✅ except camera view | ✅ all |

Both ride the **same uXRCE/ros_gz topic graph** already integrated — they only *subscribe*, so
they add no risk to the pipeline.
