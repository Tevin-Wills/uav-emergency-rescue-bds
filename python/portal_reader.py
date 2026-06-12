"""
portal_reader.py — GCS Layer 1: polls the BDS-SMC portal for received short messages.

The portal (bdrd.hwasmart.com) is a browser SPA backed by an API server at
bdrdserver.hwasmart.com. Authentication is an SSO code flow, so this reader does
NOT automate the password login. Instead it reuses the browser session tokens:

  One-time setup (per token expiry):
    1. Log in at http://bdrd.hwasmart.com in a browser.
    2. Press F12 -> Application tab -> Local Storage -> http://bdrdserver.hwasmart.com
       (open the short-message app first so its storage exists).
    3. Copy the values of:  data  (this is your uid),  access_token,  refresh_token
    4. Paste them into portal_config.json next to this script (template auto-created
       on first run).

  After that the reader refreshes its own tokens via /authentication/getToken
  (refresh_token grant) and rewrites portal_config.json, so the browser step is
  only needed again if the refresh token itself expires.

API endpoints (reverse-engineered from the portal's JS bundle, 2026-06-12):
    POST /authentication/verify      {access_token, data:<uid>}        -> code 200 if valid
    POST /authentication/getToken    {code:<refresh_token>, type:<uid>} -> new token pair
    POST /bdShortMessage/getRecord   {uid, offset, limit, searchOptions, sortOptions}
                                     -> {code:200, recordMsg:[...], count:N}
    POST /bdShortMessage/getHistoryMsg  (same shape) -> {code:200, historyMsg:[...], count:N}
    All authenticated requests carry headers:  uid: <uid>, authorization: <access_token>

Output: new (unseen) messages are printed and appended to data/portal_inbox.csv.
Seen-message state is kept in data/portal_seen.json so restarts do not re-emit.

Usage:
    python portal_reader.py --once          # single poll, print new messages
    python portal_reader.py --poll 10       # poll every 10 s until Ctrl+C
    python portal_reader.py --dump          # print full raw JSON of one poll (field discovery)
    python portal_reader.py --endpoint getHistoryMsg --once
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE_URL = "http://bdrdserver.hwasmart.com"
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "portal_config.json")
DATA_DIR = os.path.join(HERE, "..", "data")
INBOX_CSV = os.path.join(DATA_DIR, "portal_inbox.csv")
SEEN_PATH = os.path.join(DATA_DIR, "portal_seen.json")

CONFIG_TEMPLATE = {
    "uid": "PASTE localStorage 'data' VALUE HERE",
    "access_token": "PASTE localStorage 'access_token' HERE",
    "refresh_token": "PASTE localStorage 'refresh_token' HERE",
}


# ── HTTP layer ────────────────────────────────────────────────

def api_post(path, body, headers=None, timeout=30):
    """POST JSON to the portal API. Returns parsed JSON dict."""
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class Portal:
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self.cfg = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            with open(self.config_path, "w") as f:
                json.dump(CONFIG_TEMPLATE, f, indent=2)
            sys.exit(
                f"[SETUP] Created {self.config_path}.\n"
                "        Log in at http://bdrd.hwasmart.com, copy data/access_token/"
                "refresh_token\n        from browser localStorage into it, then re-run."
            )
        with open(self.config_path) as f:
            cfg = json.load(f)
        if "PASTE" in cfg.get("uid", "PASTE"):
            sys.exit(f"[SETUP] {self.config_path} still has placeholder values — fill it in first.")
        return cfg

    def _save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.cfg, f, indent=2)

    def _auth_headers(self):
        return {"uid": self.cfg["uid"], "authorization": self.cfg["access_token"]}

    def refresh_tokens(self):
        """Exchange refresh_token for a new token pair (mirrors the SPA's flow)."""
        body = {"code": self.cfg["refresh_token"], "type": self.cfg["uid"]}
        resp = api_post("/authentication/getToken", body)
        if resp.get("code") != 200:
            sys.exit(
                f"[AUTH] Token refresh failed ({resp}). Re-do the browser login and "
                f"update {self.config_path}."
            )
        self.cfg["uid"] = resp.get("data", self.cfg["uid"])
        self.cfg["access_token"] = resp["access_token"]
        self.cfg["refresh_token"] = resp.get("refresh_token", self.cfg["refresh_token"])
        self._save_config()
        print("[AUTH] Tokens refreshed.")

    def fetch_messages(self, endpoint="getRecord", offset=0, limit=50):
        """Fetch one page of messages; auto-refreshes tokens once on auth failure."""
        body = {
            "uid": self.cfg["uid"],
            "offset": offset,
            "limit": limit,
            "searchOptions": {},
            "sortOptions": {},
        }
        for attempt in (1, 2):
            try:
                resp = api_post(f"/bdShortMessage/{endpoint}", body,
                                headers=self._auth_headers())
            except urllib.error.HTTPError as e:
                if e.code in (401, 403) and attempt == 1:
                    self.refresh_tokens()
                    continue
                raise
            if resp.get("code") == 200:
                return resp
            if attempt == 1:  # expired token often comes back as a non-200 body code
                self.refresh_tokens()
                continue
            raise RuntimeError(f"Portal returned error: {resp}")


# ── message handling ──────────────────────────────────────────

def extract_rows(resp):
    """Pull the message list out of either endpoint's response shape."""
    return resp.get("recordMsg") or resp.get("historyMsg") or []


def row_key(row):
    """Stable identity for de-duplication. Prefer a real id; fall back to content hash."""
    for k in ("id", "_id", "msg_id", "msgId"):
        if k in row:
            return str(row[k])
    return str(hash(json.dumps(row, sort_keys=True, ensure_ascii=False)))


def load_seen():
    if os.path.exists(SEEN_PATH):
        with open(SEEN_PATH) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_PATH, "w") as f:
        json.dump(sorted(seen), f)


def append_inbox(rows):
    """Append new rows to the inbox CSV (raw JSON per row; columns may vary by portal)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    new_file = not os.path.exists(INBOX_CSV)
    with open(INBOX_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["received_at_local", "row_json"])
        for row in rows:
            w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"),
                        json.dumps(row, ensure_ascii=False)])


def poll_once(portal, endpoint, seen, dump=False):
    resp = portal.fetch_messages(endpoint=endpoint)
    if dump:
        print(json.dumps(resp, indent=2, ensure_ascii=False))
        return []
    rows = extract_rows(resp)
    new = [r for r in rows if row_key(r) not in seen]
    for r in new:
        seen.add(row_key(r))
        print(f"[NEW MSG] {json.dumps(r, ensure_ascii=False)}")
    if new:
        append_inbox(new)
        save_seen(seen)
    return new


def main():
    ap = argparse.ArgumentParser(description="Poll the BDS-SMC portal for received messages.")
    ap.add_argument("--once", action="store_true", help="poll once and exit")
    ap.add_argument("--poll", type=float, metavar="SEC", help="poll continuously every SEC seconds")
    ap.add_argument("--dump", action="store_true", help="print one full raw API response and exit")
    ap.add_argument("--endpoint", default="getRecord", choices=["getRecord", "getHistoryMsg"])
    args = ap.parse_args()

    portal = Portal()
    seen = load_seen()

    if args.dump:
        poll_once(portal, args.endpoint, seen, dump=True)
        return
    if args.once or not args.poll:
        n = poll_once(portal, args.endpoint, seen)
        print(f"[DONE] {len(n)} new message(s).")
        return

    print(f"[POLL] every {args.poll}s on /bdShortMessage/{args.endpoint} — Ctrl+C to stop")
    while True:
        try:
            poll_once(portal, args.endpoint, seen)
        except Exception as e:
            print(f"[WARN] poll failed: {e} — retrying next cycle")
        time.sleep(args.poll)


if __name__ == "__main__":
    main()
