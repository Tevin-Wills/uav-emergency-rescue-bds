"""
tx_dashboard.py — GCS transmission status dashboard for BDS-SMC2.

Shows every transmission's lifecycle in a browser, merging the two logs the
system already produces:

  TX side (node → satellite):  data/gap2_latency.csv   (serial_logger.py)
      [T1] sent  →  [T2] module ACK  →  [T3] satellite ACK / timeout
  RX side (satellite → ground): data/portal_inbox.csv  (portal_reader.py)
      message confirmed received by the operator portal, decoded if binary

Per-message stages displayed:
  SENT → ACCEPTED (T2) → SAT ACK (T3) | TIMEOUT → GROUND CONFIRMED → DECODED

A TX is matched to a portal RX when the portal receive time falls within
MATCH_WINDOW_S of the TX time (best effort until per-message IDs exist).

Usage:
    python tx_dashboard.py                 # serve on http://localhost:8765
    python tx_dashboard.py --port 9000
Auto-refreshes every 5 s — leave it open during a field session.
Stdlib only (http.server); no installs needed.
"""

import argparse
import csv
import json
import os
import struct
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
TX_CSV = os.path.join(HERE, "..", "data", "gap2_latency.csv")
RX_CSV = os.path.join(HERE, "..", "data", "portal_inbox.csv")
LIVE_JSON = os.path.join(HERE, "..", "data", "live_state.json")
MATCH_WINDOW_S = 90

SIM = False           # --sim: presentation mode, synthesises a live TX cycle
SIM_T0 = time.time()
SIM_CYCLE_S = 12.0    # one simulated transmission every 12 s
SIM_RECORDS = [       # lab rescue report T001-T006 (Table 5)
    (49.0068822, 8.4383287, 114, 160, 1, 1),
    (49.0070078, 8.4382004, 114, 1190, 2, 2),
    (49.0070315, 8.4375595, 114, 460, 2, 3),
    (49.0070212, 8.4376131, 115, 160, 0, 4),
    (49.0071041, 8.4371681, 114, 330, 0, 5),
    (49.0071067, 8.4371963, 114, 200, 2, 6),
]


# ── decode (mirrors decode_binary.py / firmware) ─────────────

def try_decode(text):
    """If the message text contains BIN:<hex>, decode the rescue payload."""
    if not text or "BIN:" not in text:
        return None
    try:
        hex_str = text.split("BIN:")[1].split("*")[0].strip()
        raw = bytes.fromhex(hex_str)
        if len(raw) == 14:
            lat, lon, alt, r_cm, pri, sid = struct.unpack(">iihHBB", raw)
            return (f"T{sid:03d}  {lat/1e7:.7f}, {lon/1e7:.7f}, "
                    f"{alt}m, R{r_cm/100:.1f}m, P{pri}")
        if len(raw) == 8:
            lat, lon = struct.unpack(">ii", raw)
            return f"{lat/1e4:.4f}, {lon/1e4:.4f} (legacy 64-bit)"
    except Exception:
        pass
    return None


# ── data loading ──────────────────────────────────────────────

def load_tx():
    """TX events from the serial logger CSV."""
    if not os.path.exists(TX_CSV):
        return []
    out = []
    with open(TX_CSV, newline="") as f:
        for r in csv.DictReader(f):
            ok = r.get("t3", "") not in ("", None) and r.get("total_latency_ms") != "-1"
            try:
                ts = datetime.fromisoformat(r["datetime"])
            except (KeyError, ValueError):
                ts = None
            payload = r.get("payload", "") or ""
            hex_sent = ""
            if "BIN:" in payload:
                hex_sent = payload.split("BIN:")[1].split("*")[0].strip().upper()
            out.append({
                "tx_num": r.get("tx_num", "?"),
                "session": r.get("session", ""),
                "time": r.get("datetime", ""),
                "ts": ts.timestamp() if ts else None,
                "t2": bool(r.get("t2")),
                "t3": ok,
                "latency_ms": r.get("tx_latency_ms", ""),  # same column the paper reports
                "status": "SAT ACK" if ok else "TIMEOUT",
                "payload": payload,
                "hex": hex_sent,
                "sent": try_decode(payload) or (payload[:60] if payload else ""),
            })
    return out


def load_rx():
    """RX confirmations pulled from the portal by portal_reader.py."""
    if not os.path.exists(RX_CSV):
        return []
    out = []
    with open(RX_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                row = json.loads(r["row_json"])
            except (KeyError, ValueError):
                row = {}
            # message text field name varies by portal — try common keys
            text = next((str(row[k]) for k in
                         ("content", "message", "msg", "raw", "text", "data")
                         if k in row and row[k]), json.dumps(row, ensure_ascii=False)[:120])
            try:
                ts = datetime.strptime(r["received_at_local"], "%Y-%m-%d %H:%M:%S")
            except (KeyError, ValueError):
                ts = None
            out.append({
                "time": r.get("received_at_local", ""),
                "ts": ts.timestamp() if ts else None,
                "text": text,
                "decoded": try_decode(text),
            })
    return out


def load_live():
    """In-flight TX state published by serial_logger.py (real hardware mode)."""
    try:
        with open(LIVE_JSON) as f:
            live = json.load(f)
        if live.get("state") == "in_flight" and time.time() - live.get("updated", 0) < 40:
            live["sent"] = try_decode(live.get("payload", "")) or ""
            return live
    except Exception:
        pass
    return None


def _sim_payload(rec):
    lat, lon, alt, r_cm, pri, sid = rec
    hx = struct.pack(">iihHBB", round(lat * 1e7), round(lon * 1e7),
                     alt, r_cm, pri, sid).hex().upper()
    return f"$CCTXM,0,BIN:{hx}*4C"


def sim_state():
    """Deterministic presentation animation: a TX every SIM_CYCLE_S seconds.
    Phase 0-0.4s: loaded · 0.4-2.5s: module acked, waiting on satellite ·
    2.5s: satellite ACK (row completes) · ~6s: portal confirms (row turns green)."""
    el = time.time() - SIM_T0
    ncomplete = int(el // SIM_CYCLE_S)
    phase = el % SIM_CYCLE_S

    tx, rx = [], []
    for i in range(max(0, ncomplete - 20), ncomplete):
        rec = SIM_RECORDS[i % 6]
        payload = _sim_payload(rec)
        t_fire = SIM_T0 + i * SIM_CYCLE_S
        lat_ms = 1800 + (i * 397) % 2200
        portal_dt = 4.0 + ((i * 131) % 40) / 10
        confirmed = (el - (i * SIM_CYCLE_S)) > 2.5 + portal_dt
        decoded = try_decode(payload)
        tx.append({
            "tx_num": str(i + 1), "session": "demo",
            "time": datetime.fromtimestamp(t_fire).isoformat(),
            "ts": t_fire, "t2": True, "t3": True,
            "latency_ms": str(lat_ms), "status": "SAT ACK",
            "payload": payload, "hex": payload.split("BIN:")[1].split("*")[0],
            "sent": decoded,
            "confirmed": confirmed, "integrity": confirmed,
            "rx_text": ("bit-perfect · " + decoded) if confirmed else "",
            "portal_dt_s": portal_dt if confirmed else None,
        })
        if confirmed:
            rx.append({"time": datetime.fromtimestamp(t_fire + 2.5 + portal_dt)
                              .strftime("%Y-%m-%d %H:%M:%S"),
                       "ts": t_fire + 2.5 + portal_dt,
                       "text": payload, "decoded": decoded})

    live = None
    if phase < 2.5:  # current TX still climbing to the satellite
        rec = SIM_RECORDS[ncomplete % 6]
        payload = _sim_payload(rec)
        live = {"state": "in_flight", "tx_num": ncomplete + 1, "session": "demo",
                "t1": True, "t2": phase > 0.4, "t3": False,
                "payload": payload, "sent": try_decode(payload)}
    return tx, rx, live


def build_state():
    if SIM:
        tx, rx, live = sim_state()
        tx_n = len(tx)
        lats = [int(t["latency_ms"]) for t in tx]
        return {
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "  ·  SIMULATION",
            "live": live,
            "summary": {
                "total_tx": tx_n, "sat_ack": tx_n, "timeouts": 0,
                "ground_confirmed": sum(1 for t in tx if t["confirmed"]),
                "bit_perfect": sum(1 for t in tx if t["integrity"]),
                "mean_latency_ms": round(sum(lats) / len(lats)) if lats else None,
                "portal_rows": len(rx),
            },
            "tx": tx[::-1][:200], "rx": rx[::-1][:50],
        }
    tx, rx = load_tx(), load_rx()
    used = set()
    for t in tx:  # match each successful TX to the nearest unmatched portal RX
        t["confirmed"] = False
        t["integrity"] = False
        t["rx_text"] = ""
        t["portal_dt_s"] = None
        if not t["t3"] or t["ts"] is None:
            continue
        # Pass 1 — payload-content match: portal row contains the exact sent hex
        # (proves the received bytes equal the sent bytes: bit-perfect integrity).
        # Nearest-in-time among content matches, since repeated TXs share a payload.
        best, best_dt = None, MATCH_WINDOW_S
        if t["hex"]:
            for i, r in enumerate(rx):
                if i in used or r["ts"] is None:
                    continue
                if t["hex"] in r["text"].upper().replace(" ", ""):
                    dt = abs(r["ts"] - t["ts"])
                    if best is None or dt < best_dt:
                        best, best_dt = i, dt
            if best is not None:
                used.add(best)
                t["confirmed"] = True
                t["integrity"] = True
                t["rx_text"] = "bit-perfect · " + (rx[best]["decoded"] or rx[best]["text"])
                # black-box transit (upper bound — includes up to one poll interval)
                t["portal_dt_s"] = round(rx[best]["ts"] - t["ts"], 1) if rx[best]["ts"] and t["ts"] else None
                continue
        # Pass 2 — fall back to time-window match (no payload recorded, or
        # portal reformats the content)
        best, best_dt = None, MATCH_WINDOW_S
        for i, r in enumerate(rx):
            if i in used or r["ts"] is None:
                continue
            dt = abs(r["ts"] - t["ts"])
            if dt <= best_dt:
                best, best_dt = i, dt
        if best is not None:
            used.add(best)
            t["confirmed"] = True
            t["rx_text"] = rx[best]["decoded"] or rx[best]["text"]
            t["portal_dt_s"] = round(rx[best]["ts"] - t["ts"], 1) if rx[best]["ts"] and t["ts"] else None

    n = len(tx)
    ok = sum(1 for t in tx if t["t3"])
    lats = [int(t["latency_ms"]) for t in tx if t["t3"] and str(t["latency_ms"]).lstrip("-").isdigit()]
    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "live": load_live(),
        "summary": {
            "total_tx": n,
            "sat_ack": ok,
            "timeouts": n - ok,
            "ground_confirmed": sum(1 for t in tx if t.get("confirmed")),
            "bit_perfect": sum(1 for t in tx if t.get("integrity")),
            "mean_latency_ms": round(sum(lats) / len(lats)) if lats else None,
            "portal_rows": len(rx),
        },
        "tx": tx[::-1][:200],   # newest first
        "rx": rx[::-1][:50],
    }


# ── web server ────────────────────────────────────────────────

PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>BDS-SMC2 Transmission Dashboard</title><style>
body{background:#10141a;color:#dde3ea;font-family:Segoe UI,Arial,sans-serif;margin:0;padding:20px}
h1{font-size:20px;margin:0 0 4px} .sub{color:#7a8696;font-size:12px;margin-bottom:16px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.card{background:#1a212b;border-radius:8px;padding:12px 18px;min-width:110px}
.card .v{font-size:26px;font-weight:700} .card .k{font-size:11px;color:#7a8696;text-transform:uppercase}
table{border-collapse:collapse;width:100%;font-size:13px}
th{color:#7a8696;text-align:left;padding:6px 10px;border-bottom:1px solid #2a3442;font-size:11px;text-transform:uppercase}
td{padding:6px 10px;border-bottom:1px solid #1d2531}
.pill{padding:2px 9px;border-radius:10px;font-size:11px;font-weight:600}
.ok{background:#11391f;color:#4ade80}.bad{background:#3a1418;color:#f87171}
.mid{background:#332b10;color:#fbbf24}.gray{background:#242c37;color:#8d99a8}
.stages span{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}
.on{background:#4ade80}.off{background:#37404d}
.next{background:#fbbf24;animation:pulse 0.9s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.25}}
.liverow td{background:#1c2433;border-top:1px solid #fbbf24;border-bottom:1px solid #fbbf24}
h2{font-size:14px;color:#9fb0c3;margin:26px 0 8px}
.mono{font-family:Consolas,monospace;font-size:12px;color:#9fb0c3}
</style></head><body>
<h1>BDS-SMC2 — Transmission Status</h1>
<div class="sub">node → satellite → portal &nbsp;·&nbsp; live, refresh 1.5 s &nbsp;·&nbsp; <span id="gen"></span></div>
<div class="cards" id="cards"></div>
<h2>Transmissions (newest first) — payload journey: loaded · module ack · satellite ack · received (portal)</h2>
<table><thead><tr><th>TX#</th><th>Session</th><th>Time</th><th>Journey</th><th>Status</th>
<th>Latency (T1→T3)</th><th>Black-box Δt</th><th>Received payload (decoded)</th></tr></thead><tbody id="txb"></tbody></table>
<h2>Portal inbox (satellite → ground station)</h2>
<table><thead><tr><th>Received</th><th>Message</th><th>Decoded rescue payload</th></tr></thead><tbody id="rxb"></tbody></table>
<script>
function dot(on){return '<span class="'+(on?'on':'off')+'"></span>'}
async function load(){
  const d = await (await fetch('/api/data')).json();
  document.getElementById('gen').textContent = 'updated ' + d.generated;
  const s = d.summary;
  const cards = [['Total TX',s.total_tx],['Sat ACK',s.sat_ack],['Timeouts',s.timeouts],
    ['Ground confirmed',s.ground_confirmed],['Bit-perfect',s.bit_perfect],
    ['Mean latency',s.mean_latency_ms? s.mean_latency_ms+' ms':'—'],
    ['Portal rows',s.portal_rows]];
  document.getElementById('cards').innerHTML = cards.map(c=>
    '<div class="card"><div class="v">'+c[1]+'</div><div class="k">'+c[0]+'</div></div>').join('');
  let liveRow = '';
  if (d.live) {
    const L = d.live;
    const dots = dot(L.t1) + (L.t2? dot(true) : '<span class="next"></span>') +
                 (L.t2? '<span class="next"></span>' : dot(false)) + dot(false);
    liveRow = '<tr class="liverow"><td>'+L.tx_num+'</td><td>'+L.session+
      '</td><td class="mono">— now —</td><td class="stages">'+dots+
      '</td><td><span class="pill mid">IN FLIGHT</span></td><td class="mono">…</td><td>—</td>'+
      '<td class="mono">'+(L.sent? 'loaded: '+L.sent : 'payload loading…')+'</td></tr>';
  }
  document.getElementById('txb').innerHTML = liveRow + d.tx.map(t=>{
    const st = t.t3 ? (t.integrity?'<span class="pill ok">CONFIRMED ✓</span>'
                      :(t.confirmed?'<span class="pill ok">CONFIRMED</span>':'<span class="pill mid">SAT ACK</span>'))
                    : '<span class="pill bad">TIMEOUT</span>';
    const right = t.rx_text || (t.sent? '<span style="color:#5a6675">sent: '+t.sent+'</span>' : '—');
    const bbox = (t.portal_dt_s!==null && t.portal_dt_s!==undefined)? '&le; '+t.portal_dt_s+' s' : '—';
    return '<tr><td>'+t.tx_num+'</td><td>'+t.session+'</td><td class="mono">'+t.time.replace('T',' ').slice(0,19)+
      '</td><td class="stages">'+dot(true)+dot(t.t2)+dot(t.t3)+dot(t.confirmed)+'</td><td>'+st+
      '</td><td>'+(t.t3? t.latency_ms+' ms':'—')+'</td><td class="mono">'+bbox+'</td><td class="mono">'+right+'</td></tr>';
  }).join('');
  document.getElementById('rxb').innerHTML = d.rx.length ? d.rx.map(r=>
    '<tr><td class="mono">'+r.time+'</td><td class="mono">'+r.text+'</td><td class="mono">'+(r.decoded||'—')+'</td></tr>'
  ).join('') : '<tr><td colspan="3" style="color:#5a6675">No portal data yet — run portal_reader.py --poll 10 alongside this dashboard</td></tr>';
}
load(); setInterval(load, 1500);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            body = json.dumps(build_state()).encode("utf-8")
            ctype = "application/json"
        else:
            body = PAGE.encode("utf-8")
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence per-request console spam
        pass


def main():
    global SIM, SIM_T0
    ap = argparse.ArgumentParser(description="BDS-SMC2 transmission status dashboard")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--sim", action="store_true",
                    help="presentation mode: animates a simulated TX cycle (T001-T006), "
                         "no hardware or data files needed")
    args = ap.parse_args()
    SIM, SIM_T0 = args.sim, time.time()
    mode = "SIMULATION (presentation)" if SIM else "live data"
    print(f"[DASHBOARD] http://localhost:{args.port}  ({mode}; Ctrl+C to stop)")
    if not SIM:
        print(f"[DASHBOARD] TX log : {os.path.normpath(TX_CSV)}")
        print(f"[DASHBOARD] RX log : {os.path.normpath(RX_CSV)}")
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
