# Message Formats

## Purpose

This file defines standard message structures for all data exchanged between the five project modules. These formats must be agreed upon before implementation to guarantee integration compatibility.

---

## 1. UAV Position Message

Published by: `rtk_positioning`
Subscribed by: `path_planning`, `qgc_control`

```json
{
  "uav_id": "UAV_01",
  "latitude": 39.98110,
  "longitude": 116.34720,
  "altitude": 60.0,
  "position_mode": "RTK_FIXED",
  "horizontal_error_m": 0.05,
  "timestamp": "2026-05-18T14:30:05"
}
```

---

## 2. RTK-Corrected Position Message

Published by: `rtk_positioning` (after RTCM correction applied)
Subscribed by: `path_planning`, `qgc_control`

Same structure as UAV Position Message with `position_mode` set to `RTK_FIXED` or `RTK_FLOAT`.

---

## 3. Emergency Target Coordinate

Published by: `beidou_short_message`
Subscribed by: `qgc_control`, `path_planning`

```json
{
  "target_id": "TARGET_001",
  "latitude": 39.98125,
  "longitude": 116.34788,
  "altitude": 42.0,
  "priority": "urgent",
  "source": "beidou_short_message",
  "timestamp": "2026-05-18T14:30:00"
}
```

---

## 4. Target Detection Result

Published by: `target_detection_tracking`
Subscribed by: `path_planning`

```json
{
  "detected": true,
  "confidence": 0.93,
  "bounding_box": {
    "x": 320,
    "y": 240,
    "width": 80,
    "height": 80
  },
  "timestamp": "2026-05-18T14:31:00"
}
```

---

## 5. Path Planning Output

Published by: `path_planning`
Subscribed by: `qgc_control`

```json
{
  "path_id": "PATH_001",
  "waypoints": [
    {"latitude": 39.98110, "longitude": 116.34720, "altitude": 60.0},
    {"latitude": 39.98115, "longitude": 116.34740, "altitude": 58.0},
    {"latitude": 39.98125, "longitude": 116.34788, "altitude": 42.0}
  ],
  "status": "planned",
  "timestamp": "2026-05-18T14:30:10"
}
```

---

## 6. Mission Status

Published by: `qgc_control`
Subscribed by: All modules

```json
{
  "mission_id": "MISSION_001",
  "phase": "IN_FLIGHT",
  "active_waypoint": 2,
  "timestamp": "2026-05-18T14:31:30"
}
```

Phase values: `IDLE`, `DISTRESS_RECEIVED`, `MISSION_PLANNED`, `PRE_FLIGHT`, `IN_FLIGHT`, `TARGET_ACQUIRED`, `LANDING`, `MISSION_COMPLETE`

---

## 7. BeiDou Short Message

Published by: `beidou_short_message`
Subscribed by: `qgc_control`

```json
{
  "message_id": "BDS_0042",
  "sender_id": "RESCUE_BASE_01",
  "raw_message": "SOS:39.98125N116.34788E",
  "decoded_latitude": 39.98125,
  "decoded_longitude": 116.34788,
  "received_at": "2026-05-18T14:29:58"
}
```

---

## Notes

- All timestamps are ISO 8601 UTC.
- Coordinates always use WGS84 decimal degrees. See [`coordinate_format.md`](coordinate_format.md).
- ROS 2 custom message definitions (.msg files) live in `ros2_ws/src/interfaces/msg/`.
- Update this file whenever a message format changes — all team members must be notified.
