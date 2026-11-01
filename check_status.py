#!/usr/bin/env python3
"""
Status Code Monitor - checker script.
Reads hosts.json, checks each URL, tracks redirects, and appends
active/inactive time + a timestamped history entry to status-history.json.
Meant to be run on a schedule by .github/workflows/status-check.yml.
"""
import json
import os
import time
from datetime import datetime, timezone

import requests

HOSTS_FILE = "hosts.json"
HISTORY_FILE = "status-history.json"
TIMEOUT = 10


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def check(url):
    start = time.time()
    try:
        resp = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        elapsed_ms = round((time.time() - start) * 1000)
        redirected = len(resp.history) > 0
        return {
            "status": resp.status_code,
            "ok": 200 <= resp.status_code < 400,
            "responseTimeMs": elapsed_ms,
            "redirected": redirected,
            "finalUrl": resp.url if redirected else None,
            "redirectChain": [r.url for r in resp.history] if redirected else [],
        }
    except requests.RequestException as e:
        return {
            "status": "error",
            "ok": False,
            "responseTimeMs": None,
            "redirected": False,
            "finalUrl": None,
            "redirectChain": [],
            "error": str(e),
        }


def main():
    hosts = load_json(HOSTS_FILE, [])
    history = load_json(HISTORY_FILE, {})
    now = datetime.now(timezone.utc).isoformat()

    for url in hosts:
        entry = history.get(url, {
            "monitorStart": now,
            "activeMs": 0,
            "inactiveMs": 0,
            "lastCheck": None,
            "redirectCount": 0,
            "checks": [],
        })

        # Add elapsed time since the last check to the running active/inactive total,
        # based on the status observed at that last check.
        if entry["lastCheck"]:
            prev_time = datetime.fromisoformat(entry["lastCheck"])
            delta_ms = (datetime.now(timezone.utc) - prev_time).total_seconds() * 1000
            was_ok = entry["checks"][-1]["ok"] if entry["checks"] else None
            if was_ok is True:
                entry["activeMs"] += delta_ms
            elif was_ok is False:
                entry["inactiveMs"] += delta_ms

        result = check(url)
        if result["redirected"]:
            entry["redirectCount"] += 1

        entry["checks"].append({"time": now, **result})
        entry["checks"] = entry["checks"][-200:]  # keep history file bounded
        entry["lastCheck"] = now
        history[url] = entry

    save_json(HISTORY_FILE, history)


if __name__ == "__main__":
    main()
