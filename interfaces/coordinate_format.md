# Coordinate Format Standard

## Purpose

This file defines the standard coordinate format that all five modules must use when exchanging position data. Using a consistent format prevents unit mismatches and integration errors.

---

## Standard UAV Position Format

All position data shared between modules uses the following JSON-compatible structure:

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

### Fields

| Field | Unit | Description |
|---|---|---|
| `uav_id` | string | Unique identifier for the UAV |
| `latitude` | decimal degrees (WGS84) | Positive = North |
| `longitude` | decimal degrees (WGS84) | Positive = East |
| `altitude` | metres above mean sea level | Ellipsoidal height from GNSS |
| `position_mode` | string | `RTK_FIXED`, `RTK_FLOAT`, `GPS_ONLY`, `UNKNOWN` |
| `horizontal_error_m` | metres | Estimated horizontal positioning error |
| `timestamp` | ISO 8601 UTC | Format: `YYYY-MM-DDTHH:MM:SS` |

---

## Emergency Target Coordinate Format

Rescue target coordinates provided by the BeiDou short message module:

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

### Fields

| Field | Unit | Description |
|---|---|---|
| `target_id` | string | Unique identifier for this rescue target |
| `latitude` | decimal degrees (WGS84) | Target latitude |
| `longitude` | decimal degrees (WGS84) | Target longitude |
| `altitude` | metres | Target estimated altitude (surface level if unknown) |
| `priority` | string | `urgent`, `normal`, `low` |
| `source` | string | Origin of the coordinate (`beidou_short_message`, `manual`, etc.) |
| `timestamp` | ISO 8601 UTC | When the coordinate was generated |

---

## Rules

- Always use WGS84 as the geodetic datum.
- Altitude is always metres above mean sea level (AMSL) unless explicitly stated otherwise.
- Timestamps must be UTC. Do not use local time.
- `position_mode` must always be populated — never leave it blank or unknown if avoidable.
- Coordinate accuracy for RTK Fixed mode is expected to be ≤ 0.05 m horizontal.

---

## ROS 2 Equivalent

When publishing positions as ROS 2 messages, use `sensor_msgs/NavSatFix` for raw GNSS and `geometry_msgs/PoseStamped` for transformed positions in the local frame. Custom message definitions are in `ros2_ws/src/interfaces/`.
