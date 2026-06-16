"""
gcs/main.py — Ground Control Station entry point.

Runs the 4-layer chain on whatever is in the portal store:
    portal reader -> decoder (detect) -> display (map) -> export (waypoint)

Source of messages:
    --source sim    (default) read sim/virtual_portal PortalStore (data/portal_inbox_sim.csv)
    --source live   read the real portal inbox (data/portal_inbox.csv from portal_reader.py)

Outputs gcs/output/map.html and gcs/output/survivor.waypoints, and prints the ROS 2
EmergencyCoordinate mapping for each survivor.
"""

import argparse
import csv
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))            # repo root
sys.path.insert(0, os.path.join(HERE, "..", "sim"))     # virtual_portal

from gcs.decoder.detect import detect_and_decode, PRIORITY_LABEL
from gcs.display import map_view
from gcs.export import waypoint

LIVE_INBOX = os.path.join(HERE, "..", "data", "portal_inbox.csv")


def _read_inbox(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                out.append(json.loads(row["row_json"]))
            except Exception:
                pass
    return out


def run(source="sim"):
    if source == "sim":
        from virtual_portal import PortalStore
        records = PortalStore().records()
    else:
        records = _read_inbox(LIVE_INBOX)

    print(f"[GCS] {len(records)} portal record(s) from '{source}' source\n")
    survivors = []
    for r in records:
        dec = detect_and_decode(r.get("msg_data"))
        if dec["type"] in ("binary", "ascii") and dec["lat"] is not None:
            dec["created_at"] = r.get("created_at", "")
            survivors.append(dec)
            print(f"  ✓ T{(dec['survivor_id'] or 0):03d}  "
                  f"{dec['lat']:.7f}, {dec['lon']:.7f}  "
                  f"alt={dec['alt_m']}m R={(dec['r_cm'] or 0)/100:.2f}m  "
                  f"{PRIORITY_LABEL.get(dec['priority'], '-')}  [{dec['bits']}-bit]")
        else:
            print(f"  · skipped non-coordinate msg: {r.get('msg_data')!r} ({dec['type']})")

    if not survivors:
        print("\n[GCS] no decodable survivor coordinates — nothing to dispatch.")
        return

    map_path = map_view.render(survivors)
    wp_path = waypoint.write_waypoints(survivors)
    print(f"\n[GCS] map  -> {map_path}")
    print(f"[GCS] mission -> {wp_path}")
    print("\n[GCS] ROS 2 /target/emergency_coordinate dispatch:")
    for s in survivors:
        ec = waypoint.to_emergency_coordinate(s)
        print(f"   {json.dumps(ec, ensure_ascii=False)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["sim", "live"], default="sim")
    run(ap.parse_args().source)
