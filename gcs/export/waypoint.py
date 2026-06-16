"""
waypoint.py — GCS Layer 4: convert a decoded survivor coordinate into a UAV tasking.

Outputs:
  * a QGC WPL 110 .waypoints file (loadable by QGroundControl / Mission Planner)
  * the matching ROS 2 EmergencyCoordinate field mapping (printed / returned), per the
    group integration contract (/target/emergency_coordinate).
  * optional: a MAVLink mission-item UDP packet if pymavlink is installed (skipped
    cleanly otherwise — the file is the portable artifact).

Datum note [D]: the group sim derives distress coordinates from the Zurich datum.
The lab T001-T006 coordinates (Karlsruhe) are dissertation hardware-test values only.
"""

import os

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")


def write_waypoints(survivors, out_path=None, takeoff_alt=30.0):
    """Write a QGC WPL 110 mission: home at first survivor, then a NAV_WAYPOINT per
    survivor (ordered by priority, P0 first). Returns the written path."""
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = out_path or os.path.join(OUT_DIR, "survivor.waypoints")
    ordered = sorted(survivors, key=lambda s: (s.get("priority", 9)))

    lines = ["QGC WPL 110"]
    # index 0 = home (MAV_CMD_NAV_WAYPOINT, current=1, frame=0 global)
    h = ordered[0]
    lines.append(f"0\t1\t0\t16\t0\t0\t0\t0\t{h['lat']:.7f}\t{h['lon']:.7f}\t0.000000\t1")
    seq = 1
    for s in ordered:
        alt = s.get("alt_m") or takeoff_alt
        # frame 3 = MAV_FRAME_GLOBAL_RELATIVE_ALT, cmd 16 = NAV_WAYPOINT
        lines.append(f"{seq}\t0\t3\t16\t0\t0\t0\t0\t"
                     f"{s['lat']:.7f}\t{s['lon']:.7f}\t{float(alt):.6f}\t1")
        seq += 1
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return os.path.abspath(out_path)


def to_emergency_coordinate(s, source_id="beidou_short_message"):
    """Map a decoded survivor to the group's ROS 2 EmergencyCoordinate fields."""
    return {
        "header": {"frame_id": "map"},
        "lat": s["lat"],
        "lon": s["lon"],
        "source_id": source_id,
        "raw_message": s.get("raw", ""),
        # proposed extension fields (pending group agreement):
        "altitude": s.get("alt_m"),
        "uncertainty_m": (s.get("r_cm") or 0) / 100.0,
        "priority": s.get("priority"),
        "survivor_id": s.get("survivor_id"),
    }


def send_udp_mavlink(s, ip="127.0.0.1", port=14550):
    """Best-effort live dispatch to a MAVLink GCS. No-op (returns False) if pymavlink
    is not installed — the .waypoints file remains the portable deliverable."""
    try:
        from pymavlink import mavutil
    except Exception:
        return False
    m = mavutil.mavlink_connection(f"udpout:{ip}:{port}")
    m.mav.mission_item_int_send(
        0, 0, 0, 3, 16, 0, 1, 0, 0, 0, 0,
        int(s["lat"] * 1e7), int(s["lon"] * 1e7), float(s.get("alt_m") or 30.0))
    return True


if __name__ == "__main__":
    demo = [{"lat": 49.0068822, "lon": 8.4383287, "alt_m": 114.0, "r_cm": 160,
             "priority": 0, "survivor_id": 4, "raw": "BIN:..."}]
    print("wrote", write_waypoints(demo))
    print(to_emergency_coordinate(demo[0]))
