"""
task_board.py — live project task board for the BDS-SMC2 node (Paper 1 phase).

Serves a dark-themed board at http://localhost:8766 with four columns:
  DO NOW (no hardware) · WAITING ON OTHERS · HARDWARE DAY · DONE

Tasks live in data/task_status.json (created with current status on first run).
Edit that file — change a task's "col" to move it — and the board updates live
(auto-refresh 5 s). Allowed col values: now | waiting | hardware | done

Usage:  python task_board.py        # then open http://localhost:8766
"""

import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS_JSON = os.path.join(HERE, "..", "data", "task_status.json")

DEFAULT_TASKS = [
    # ── DO NOW (no hardware) ──
    {"col": "now", "t": "Open the PR (node/binary-decode) and tag the team", "d": "github.com/Tevin-Wills/uav-emergency-rescue-bds/pull/new/node/binary-decode", "min": "2 min"},
    {"col": "now", "t": "Portal tokens -> portal_reader.py --dump", "d": "bdrd.hwasmart.com login, F12 > Local Storage > data/access_token/refresh_token into portal_config.json", "min": "5 min"},
    {"col": "now", "t": "Message group + book .msg extension slot", "d": "Proposal pack ready: Paper1_Sections.md Section E", "min": "5 min"},
    {"col": "now", "t": "Fill [CITE] placeholders", "d": "BDS_SMC2_Paper1_Sections.md — anchor papers listed in Node_Evaluation.md", "min": "1-2 evenings"},
    {"col": "now", "t": "Write Paper 1 Sections I-IV", "d": "Intro, related work, system design, methodology — no new data needed", "min": "2-3 evenings"},
    {"col": "now", "t": "Update generate_presentation.py numbers", "d": "Still says 64/128-bit; fix before regenerating slides", "min": "30 min"},
    {"col": "now", "t": "Print field sheet + pick field day", "d": "BDS-SMC2_Field_Sheet.pdf (4 sheets); slots 08-10h, 12-14h, 18h+; optional USB power meter", "min": "10 min"},
    # ── WAITING ON OTHERS ──
    {"col": "waiting", "t": "PR review + merge by team", "d": "3-file diff inside beidou_short_message only", "min": "team"},
    {"col": "waiting", "t": ".msg extension decision", "d": "4 additive fields: altitude, uncertainty_m, priority, survivor_id", "min": "group meeting"},
    {"col": "waiting", "t": "Ubuntu integration session", "d": "colcon build + verify_integration.sh (expect 3/3)", "min": "with group"},
    # ── HARDWARE DAY (one outing) ──
    {"col": "hardware", "t": "Flash MODE 1 + morning session (30 TX)", "d": "TX #1 = 112-bit acceptance + on-air bit check; run_gap2_morning.bat", "min": "08-10h"},
    {"col": "hardware", "t": "Midday session (30 TX) + power", "d": "run_gap2_midday.bat; USB meter optional", "min": "12-14h"},
    {"col": "hardware", "t": "Evening session (30 TX)", "d": "run_gap2_evening.bat — same day", "min": "18h+"},
    {"col": "hardware", "t": "Run ANOVA + regenerate figures", "d": "gap2_analysis.py --plot; Paper 1 evidence complete", "min": "evening"},
    {"col": "hardware", "t": "Dashboard evidence screenshots", "d": "CONFIRMED bit-perfect rows + black-box dt (fixes audit risk #3)", "min": "during"},
    # ── DONE ──
    {"col": "done", "t": "112-bit rescue payload (firmware + decoders)", "d": "Round-trip bit-perfect on lab T001-T006"},
    {"col": "done", "t": "Gap 3 audited: 232/232, Wilson >=93.7%", "d": "chi2=0, p=1.0; exclusion appendix drafted from real rows"},
    {"col": "done", "t": "ROS 2 node: 3-format decode + runbook + verify script", "d": "Pushed as PR branch node/binary-decode"},
    {"col": "done", "t": "Portal API reverse-engineered + portal_reader.py", "d": "Token auth with auto-refresh; awaiting tokens"},
    {"col": "done", "t": "Live TX dashboard (+ --sim presentation mode)", "d": "Payload journey, bit-perfect matching, black-box dt, in-flight row"},
    {"col": "done", "t": "Defence sections drafted (risks 1,4,5,8,9)", "d": "Comparison table, RTK framing, Wilson claim, repeat-TX policy, .msg pack"},
    {"col": "done", "t": "Option B field plan + PDFs updated", "d": "Paper Plan Rev.2, 4-sheet field sheet, progress report; ASCII baseline archived"},
    {"col": "done", "t": "Both branches pushed to GitHub", "d": "node/bds-smc2 (workspace) + node/binary-decode (PR)"},
]

COLS = [
    ("now",      "DO NOW — NO HARDWARE", "#2e5fa3"),
    ("waiting",  "WAITING ON OTHERS",    "#b07d1a"),
    ("hardware", "HARDWARE DAY",         "#c0392b"),
    ("done",     "DONE",                 "#2d7a3a"),
]


def load_tasks():
    if not os.path.exists(TASKS_JSON):
        os.makedirs(os.path.dirname(TASKS_JSON), exist_ok=True)
        with open(TASKS_JSON, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TASKS, f, indent=1)
    with open(TASKS_JSON, encoding="utf-8") as f:
        return json.load(f)


PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>BDS-SMC2 Task Board</title><style>
body{background:#10141a;color:#dde3ea;font-family:Segoe UI,Arial,sans-serif;margin:0;padding:20px}
h1{font-size:19px;margin:0 0 2px}.sub{color:#7a8696;font-size:12px;margin-bottom:14px}
.prog{height:10px;background:#1a212b;border-radius:5px;margin-bottom:18px;overflow:hidden}
.prog div{height:100%;background:linear-gradient(90deg,#2d7a3a,#4ade80)}
.board{display:flex;gap:14px;align-items:flex-start}
.col{flex:1;background:#151b24;border-radius:10px;padding:10px;min-width:200px}
.col h2{font-size:11px;letter-spacing:1px;margin:4px 4px 10px;padding-bottom:6px;border-bottom:2px solid}
.card{background:#1c242f;border-radius:8px;padding:9px 11px;margin-bottom:8px;border-left:3px solid #37404d}
.card .t{font-size:12.5px;font-weight:600;margin-bottom:3px}
.card .d{font-size:10.5px;color:#8d99a8;line-height:1.45}
.card .m{font-size:9.5px;color:#5a87c5;margin-top:4px}
.done .card{opacity:0.75;border-left-color:#2d7a3a}.done .t{text-decoration:none;color:#9fd4ac}
</style></head><body>
<h1>BDS-SMC2 — Task Board (Paper 1 phase)</h1>
<div class="sub">edit data/task_status.json to move tasks · auto-refresh 5 s · <span id="gen"></span></div>
<div class="prog"><div id="bar" style="width:0%"></div></div>
<div class="board" id="board"></div>
<script>
async function load(){
  const d = await (await fetch('/api/tasks')).json();
  document.getElementById('gen').textContent = 'updated ' + d.generated + '  ·  ' + d.done + '/' + d.total + ' done';
  document.getElementById('bar').style.width = (100*d.done/d.total) + '%';
  document.getElementById('board').innerHTML = d.cols.map(c =>
    '<div class="col '+(c.key==='done'?'done':'')+'"><h2 style="color:'+c.color+';border-color:'+c.color+'">'+
    c.title+' ('+c.tasks.length+')</h2>'+ c.tasks.map(t =>
      '<div class="card" style="border-left-color:'+c.color+'"><div class="t">'+t.t+'</div>'+
      '<div class="d">'+(t.d||'')+'</div>'+(t.min?'<div class="m">'+t.min+'</div>':'')+'</div>').join('')+'</div>').join('');
}
load(); setInterval(load, 5000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/tasks":
            tasks = load_tasks()
            cols = [{"key": k, "title": t, "color": c,
                     "tasks": [x for x in tasks if x.get("col") == k]}
                    for k, t, c in COLS]
            body = json.dumps({
                "generated": datetime.now().strftime("%H:%M:%S"),
                "total": len(tasks),
                "done": sum(1 for x in tasks if x.get("col") == "done"),
                "cols": cols,
            }).encode("utf-8")
            ctype = "application/json"
        else:
            body = PAGE.encode("utf-8")
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("[TASK BOARD] http://localhost:8766  (Ctrl+C to stop)")
    print(f"[TASK BOARD] tasks file: {os.path.normpath(TASKS_JSON)}")
    HTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
