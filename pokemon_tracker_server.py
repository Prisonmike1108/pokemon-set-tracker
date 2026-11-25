#!/usr/bin/env python3
"""Local helper for pokemon-set-tracker.html

What it does (standard library only, nothing to install):
  * serves the tracker at http://localhost:8765/
  * fetches daily TCGplayer prices from tcgcsv.com for the page (browsers can't call
    tcgcsv.com directly because it sends no CORS headers) and caches them for an hour
  * backfills past prices from tcgcsv.com's daily archives (uses the tar that ships with
    Windows 10/11, or 7-Zip if you have it) so charts show real history
  * keeps your collection, portfolio and price history in tracker-data.json next to this
    script, so your data survives clearing the browser and can be backed up by copying it

Run:  python pokemon_tracker_server.py        (add --no-browser to skip opening a tab)
Stop: press Ctrl+C in the window
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "pokemon-set-tracker.html")
STATE = os.path.join(HERE, "tracker-data.json")
CACHE_DIR = os.path.join(HERE, ".tcgcsv-cache")
HOST, PORT = "127.0.0.1", 8765
TTL = 3600  # seconds to reuse a downloaded price file
MAX_STATE = 30 * 1024 * 1024
ALLOWED = re.compile(r"^tcgplayer/3/(groups|\d+/(products|prices))$")  # Pokemon (category 3) only
lock = threading.Lock()


def fetch_tcgcsv(path):
    """Return (bytes, stale_flag) for a tcgcsv.com path, using a small on-disk cache."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = os.path.join(CACHE_DIR, path.replace("/", "_") + ".json")
    fresh = os.path.exists(cache) and time.time() - os.path.getmtime(cache) < TTL
    if fresh:
        with open(cache, "rb") as f:
            return f.read(), False
    try:
        req = urllib.request.Request("https://tcgcsv.com/" + path, headers={"User-Agent": "pokemon-set-tracker-local/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        json.loads(data)  # make sure it is valid before caching
        with open(cache, "wb") as f:
            f.write(data)
        return data, False
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        if os.path.exists(cache):  # serve an old copy rather than nothing
            with open(cache, "rb") as f:
                return f.read(), True
        raise


# ---------------------------------------------------------------------------
# Price history backfill: tcgcsv.com publishes one small archive (.7z) per day.
# We download a day, pull out just the Pokemon price files we were asked for, cache
# them on disk (past days never change) and delete the archive again.
# ---------------------------------------------------------------------------
ARCHIVE_URL = "https://tcgcsv.com/archive/tcgplayer/prices-{date}.ppmd.7z"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_day_locks = {}
_day_locks_guard = threading.Lock()


def _extract_command(archive, dest, members):
    """Build a command that extracts `members` from a .7z using whatever this machine has."""
    for exe in ("tar", "bsdtar"):
        path = shutil.which(exe)
        if path:
            try:
                ver = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10).stdout.lower()
            except (OSError, subprocess.SubprocessError):
                continue
            if "bsdtar" in ver or "libarchive" in ver:  # GNU tar can't read .7z
                return [path, "-xf", archive, "-C", dest] + members
    for exe in ("7z", "7za", "7zr"):
        path = shutil.which(exe) or (r"C:\Program Files\7-Zip\7z.exe" if os.path.exists(r"C:\Program Files\7-Zip\7z.exe") and exe == "7z" else None)
        if path:
            return [path, "x", "-y", "-o" + dest, archive] + members
    return None


_dl_slots = threading.Semaphore(2)  # be polite to tcgcsv.com: at most 2 archive downloads at once


def download_archive(date, dest):
    """Download one day's archive, backing off if the server says we're going too fast (HTTP 429/503)."""
    req = urllib.request.Request(ARCHIVE_URL.format(date=date), headers={"User-Agent": "pokemon-set-tracker-local/1.0"})
    for attempt in range(6):
        with _dl_slots:
            try:
                with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as fh:
                    shutil.copyfileobj(r, fh)
                time.sleep(0.4)
                return
            except urllib.error.HTTPError as e:
                if e.code not in (429, 503) or attempt == 5:
                    raise
                try:
                    wait = int(e.headers.get("Retry-After") or 0)
                except ValueError:
                    wait = 0
                time.sleep(min(60, max(wait, 4 * (attempt + 1))))


def backfill_day(date, groups):
    """Return {group_id: [price rows] or None} for one past day."""
    day_dir = os.path.join(CACHE_DIR, "archive", date)
    os.makedirs(day_dir, exist_ok=True)
    with _day_locks_guard:
        lock_ = _day_locks.setdefault(date, threading.Lock())
    out, missing = {}, []
    with lock_:
        for g in groups:
            f = os.path.join(day_dir, f"{g}.json")
            if os.path.exists(f):
                with open(f, "r", encoding="utf-8") as fh:
                    out[g] = json.load(fh)
            else:
                missing.append(g)
        if missing:
            tmp = os.path.join(day_dir, "_work")
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(tmp)
            arc = os.path.join(tmp, "day.7z")
            try:
                download_archive(date, arc)
            except urllib.error.HTTPError as e:
                shutil.rmtree(tmp, ignore_errors=True)
                if e.code in (403, 404):  # no archive for that day (before they started, or not published yet)
                    for g in missing:
                        out[g] = None
                    return out
                raise
            members = [f"{date}/3/{g}/prices" for g in missing]
            cmd = _extract_command(arc, tmp, members)
            if not cmd:
                shutil.rmtree(tmp, ignore_errors=True)
                raise RuntimeError("Can't read .7z files here: install 7-Zip or use Windows 10/11 (which includes a suitable tar).")
            subprocess.run(cmd, capture_output=True, timeout=180)  # a group missing from the archive just yields no file
            for g in missing:
                src = os.path.join(tmp, date, "3", str(g), "prices")
                data = None
                if os.path.exists(src):
                    try:
                        with open(src, "r", encoding="utf-8") as fh:
                            data = json.load(fh).get("results")
                    except (ValueError, UnicodeDecodeError, AttributeError):
                        data = None  # some days' archives can't be fully decoded by every tar build; skip those days
                with open(os.path.join(day_dir, f"{g}.json"), "w", encoding="utf-8") as fh:
                    json.dump(data, fh)
                out[g] = data
            shutil.rmtree(tmp, ignore_errors=True)
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "PokemonTracker/1.0"

    def log_message(self, fmt, *args):  # keep the console quiet
        pass

    allow_cors = False

    def _origin_ok(self):
        """Only this machine's own pages may read from the helper: the tracker opened straight from its
        file (browsers send Origin: null for file:// pages) or served from localhost. Other websites can't."""
        o = self.headers.get("Origin") or ""
        return o if (o == "null" or o.startswith("http://localhost:") or o.startswith("http://127.0.0.1:")) else ""

    def _host_ok(self):  # blocks DNS-rebinding tricks: the Host header must be localhost
        return (self.headers.get("Host") or "").split(":")[0] in ("localhost", "127.0.0.1")

    def _send(self, code, body=b"", ctype="application/json", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        origin = self._origin_ok() if self.allow_cors else ""
        if origin:  # prices only; /api/state (your data) is never exposed cross-origin
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, b'{"error":"bad host"}')
        path = self.path.split("?", 1)[0]
        self.allow_cors = path == "/api/ping" or path == "/api/backfill" or path.startswith("/tcgcsv/")
        if path in ("/", "/index.html", "/pokemon-set-tracker.html"):
            try:
                with open(HTML, "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b"pokemon-set-tracker.html not found next to this script", "text/plain")
        elif path == "/api/ping":
            self._send(200, json.dumps({"ok": True}).encode())
        elif path == "/api/state":
            with lock:
                try:
                    with open(STATE, "rb") as f:
                        self._send(200, f.read())
                except OSError:
                    self._send(200, b"{}")
        elif path == "/api/backfill":
            qs = urllib.parse.parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            date = (qs.get("date") or [""])[0]
            groups = [g for g in (qs.get("groups") or [""])[0].split(",") if g.isdigit()][:8]
            if not DATE_RE.match(date) or not groups:
                return self._send(400, b'{"error":"need date=YYYY-MM-DD and groups=1,2"}')
            try:
                # tcgcsv publishes each day's file at about 20:00 UTC, so compare against the UTC date
                if datetime.date.fromisoformat(date) >= datetime.datetime.now(datetime.timezone.utc).date():
                    return self._send(400, b'{"error":"only past days"}')
                res = backfill_day(date, groups)
                self._send(200, json.dumps({"date": date, "groups": res}).encode())
            except Exception as e:  # noqa: BLE001
                self._send(502, json.dumps({"error": str(e)}).encode())
        elif path.startswith("/tcgcsv/"):
            rest = path[len("/tcgcsv/"):]
            if not ALLOWED.match(rest):
                return self._send(403, b'{"error":"path not allowed"}')
            try:
                data, stale = fetch_tcgcsv(rest)
                self._send(200, data, extra={"X-Stale": "1" if stale else "0"})
            except Exception as e:  # noqa: BLE001
                self._send(502, json.dumps({"error": str(e)}).encode())
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, b'{"error":"bad host"}')
        if self.path.split("?", 1)[0] != "/api/state":
            return self._send(404, b'{"error":"not found"}')
        # a JSON content type forces browsers to ask permission first when another website tries this
        if not (self.headers.get("Content-Type") or "").startswith("application/json") or (self.headers.get("Origin") and not self._origin_ok()):
            return self._send(403, b'{"error":"not allowed"}')
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_STATE:
            return self._send(413, b'{"error":"bad size"}')
        raw = self.rfile.read(length)
        try:
            obj = json.loads(raw)
            if not isinstance(obj, dict):
                raise ValueError("not an object")
        except ValueError:
            return self._send(400, b'{"error":"invalid json"}')
        with lock:
            tmp = STATE + ".tmp"
            with open(tmp, "wb") as f:
                f.write(raw)
            os.replace(tmp, STATE)
        self._send(200, b'{"ok":true}')


def main():
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError:
        print(f"Port {PORT} is already in use - the tracker may already be running at http://localhost:{PORT}/")
        if "--no-browser" not in sys.argv:
            webbrowser.open(f"http://localhost:{PORT}/")
        return
    url = f"http://localhost:{PORT}/"
    print(f"Pokemon Set Tracker helper running. Open pokemon-set-tracker.html as usual, or use {url}")
    print(f"Your data is saved in: {STATE}")
    print("Press Ctrl+C to stop.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
