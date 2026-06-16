"""
virtual_portal.py — local stand-in for the BeiDou ground portal (bdrdserver.hwasmart.com).

Two parts:
  * PortalStore — a file-backed record store (data/portal_inbox_sim.csv) using the SAME
    row shape as the real portal_reader.py inbox: {card_id, encode_type, msg_data,
    created_at}. Used directly by the in-process demo (sim/run_sim.py) and by gcs/main.py.
  * serve()    — an HTTP server that mimics the real API endpoints
    (/authentication/verify, /bdShortMessage/getHistoryMsg) so the UNMODIFIED
    python/portal_reader.py can poll it by pointing BASE_URL at http://127.0.0.1:8799.
    This makes the "GCS Layer 1" code path identical to the live-portal one.
"""

import csv
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
STORE_CSV = os.path.join(DATA_DIR, "portal_inbox_sim.csv")


class PortalStore:
    """Append-only record store mirroring the real portal inbox CSV."""

    def __init__(self, path=STORE_CSV):
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def post(self, record):
        """record: {card_id, encode_type, msg_data, created_at}."""
        with self._lock:
            new = not os.path.exists(self.path)
            with open(self.path, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(["received_at_local", "row_json"])
                import time
                w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"),
                            json.dumps(record, ensure_ascii=False)])

    def records(self):
        """Return all stored records (newest portal-style list)."""
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    out.append(json.loads(row["row_json"]))
                except Exception:
                    pass
        return out


# ── HTTP API (optional, for the unmodified portal_reader.py path) ─────────────

def _make_handler(store):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _json(self, obj, code=200):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            _ = self.rfile.read(n)  # body ignored; this is a stub
            if self.path.endswith("/authentication/verify"):
                return self._json({"code": 200, "data": "sim-uid-0001"})
            if self.path.endswith("/bdShortMessage/getHistoryMsg"):
                recs = store.records()
                return self._json({"code": 200, "historyMsg": recs, "count": len(recs)})
            if self.path.endswith("/bdShortMessage/getRecord"):
                recs = store.records()
                return self._json({"code": 200, "recordMsg": recs, "count": len(recs)})
            return self._json({"code": 404}, 404)
    return H


def serve(host="127.0.0.1", port=8799, store=None):
    store = store or PortalStore()
    httpd = ThreadingHTTPServer((host, port), _make_handler(store))
    print(f"[PORTAL] virtual portal on http://{host}:{port}  "
          f"(point portal_reader BASE_URL here) — Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[PORTAL] stopped")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8799)
    serve(port=ap.parse_args().port)
