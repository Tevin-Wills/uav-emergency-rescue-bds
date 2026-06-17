# Coordinate Format Standard

## Purpose

This file defines the coordinate conventions all modules must use when exchanging position
data, so there are no unit or datum mismatches. The concrete message structures are in
[`message_formats.md`](message_formats.md); topic names are in [`ros2_topics.md`](ros2_topics.md).

---

## Geodetic conventions (apply to every position)

| Field | Unit / convention |
|---|---|
| `latitude` | decimal degrees, WGS-84, positive = North |
| `longitude` | decimal degrees, WGS-84, positive = East |
| `altitude` | metres; GNSS ellipsoidal height (see datum note below) |
| timestamps | ISO 8601 **UTC** (`YYYY-MM-DDTHH:MM:SS`); never local time |

---

## System datum

The whole system shares one datum: **Zurich, `47.3980, 8.5462`** (`bringup/config/datum.yaml`,
mirrored in the RTK configs). All simulated positions — UAV, RTK base, and the BeiDou distress
coordinate (datum + offset) — are expressed relative to this datum. **Do not change it** without
updating every config together (see `docs/NATIVE_PC_RUNBOOK.md` §3).

---

## UAV position

UAV position is published as `sensor_msgs/NavSatFix` on `/uav/rtk_position` (RTK-corrected) and
`/uav/raw_gps` (raw), with `latitude`/`longitude`/`altitude` in the conventions above.

Fix quality is carried alongside on `/uav/rtk_status` (`std_msgs/String`, format
`code|name|sigma_m`). `name` is one of:

- `RTK_FIXED` — centimetre-level (expected ≤ 0.05 m horizontal)
- `RTK_FLOAT` — decimetre-level
- `GNSS_ONLY` — uncorrected GNSS
- `NO_FIX` — no valid solution

---

## Emergency target coordinate

Rescue target coordinates from the BeiDou module are published as
`interfaces/EmergencyCoordinate` on `/target/emergency_coordinate`
(`latitude`, `longitude`, `source_id`, `raw_message` + `header`). They follow the same WGS-84
decimal-degree convention. The target is derived from the system datum plus an offset, so it
stays consistent with the UAV/RTK frame.

---

## Rules

- Always use WGS-84 as the geodetic datum.
- Timestamps must be UTC.
- RTK-Fixed accuracy is expected to be ≤ 0.05 m horizontal; the landing gate
  (`/rtk/mission_viability`) enforces viability before precision landing.
- Do not introduce a second coordinate frame for shared topics; the local ENU frame
  (`px4_local_enu`, used by `/target/location`) is the only non-WGS-84 frame and is labelled
  explicitly in the message `header.frame_id`.
