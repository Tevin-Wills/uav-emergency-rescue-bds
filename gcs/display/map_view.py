"""
map_view.py — GCS Layer 3: render received survivors on a live map.

Writes a self-contained Leaflet HTML file (gcs/output/map.html) with a pin per
survivor, an uncertainty circle of radius R, and a popup carrying alt / priority /
survivor_id / message age. No Python GUI dependency — open the file in any browser.
(Tiles need internet; the markers/popups render regardless.)
"""

import json
import os

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")

_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>BDS-SMC2 Rescue GCS</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
 html,body,#map{height:100%;margin:0} #map{height:100vh}
 .hdr{position:absolute;z-index:1000;top:10px;left:50px;background:#0b1d33;color:#fff;
      padding:6px 12px;border-radius:6px;font:13px system-ui;box-shadow:0 2px 6px rgba(0,0,0,.4)}
 .pri0{color:#ff5252;font-weight:bold}.pri1{color:#ffb300}.pri2{color:#8bc34a}
</style></head><body>
<div class="hdr">🛰️ BDS-SMC2 Rescue GCS — %COUNT% survivor(s) received via BeiDou short message</div>
<div id="map"></div>
<script>
const survivors = %DATA%;
const map = L.map('map');
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {maxZoom:19, attribution:'© OpenStreetMap'}).addTo(map);
const pri = {0:['P0 URGENT','#ff5252'],1:['P1 normal','#ffb300'],2:['P2 low','#8bc34a']};
const grp = L.featureGroup().addTo(map);
survivors.forEach(s => {
  const [lbl,col] = pri[s.priority] || ['?','#3388ff'];
  L.circle([s.lat,s.lon], {radius:(s.r_cm||0)/100, color:col, weight:1,
     fillOpacity:0.12}).addTo(grp);
  L.marker([s.lat,s.lon]).addTo(grp).bindPopup(
    `<b>Survivor T${String(s.survivor_id).padStart(3,'0')}</b><br>`+
    `<span style="color:${col}">${lbl}</span><br>`+
    `lat ${s.lat.toFixed(7)}, lon ${s.lon.toFixed(7)}<br>`+
    `alt ${s.alt_m} m · R ${(s.r_cm/100).toFixed(2)} m<br>`+
    `<small>${s.bits}-bit payload · ${s.created_at||''}</small>`);
});
if (survivors.length) map.fitBounds(grp.getBounds().pad(0.5));
else map.setView([47.3980, 8.5462], 13);   // Zurich datum fallback
</script></body></html>
"""


def render(survivors, out_path=None):
    """survivors: list of dicts with lat/lon/alt_m/r_cm/priority/survivor_id/bits/created_at.
    Returns the written path."""
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = out_path or os.path.join(OUT_DIR, "map.html")
    html = (_HTML
            .replace("%DATA%", json.dumps(survivors))
            .replace("%COUNT%", str(len(survivors))))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.abspath(out_path)


if __name__ == "__main__":
    demo = [{"lat": 49.0068822, "lon": 8.4383287, "alt_m": 114.0, "r_cm": 160,
             "priority": 1, "survivor_id": 1, "bits": 112, "created_at": "demo"}]
    print("wrote", render(demo))
