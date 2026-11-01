# Status Code Monitor

A small self-hosted status monitor: a browser dashboard (`index.html`) for live,
multi-host viewing, plus a GitHub Actions workflow that checks the same hosts on
a schedule and commits history to this repo (like Upptime).

## Parts

- **`index.html`** — the dashboard. Add hosts, watch them split into a live grid,
  and see a Metrics tab with active/inactive time and redirect counts. Works
  standalone (limited to reachable/unreachable, since browsers can't read a
  cross-origin site's real status code) or against your own backend for real
  status codes — set that URL in the gear/Settings panel.
- **`hosts.json`** — the list of hosts the *scheduled* check covers.
- **`check_status.py`** — runs each check with `requests`, follows redirects,
  and appends results to `status-history.json`.
- **`.github/workflows/status-check.yml`** — runs `check_status.py` every 10
  minutes (edit the cron line to change that) and commits the updated history.
- **`status-history.json`** — created automatically on first run; per-host
  running totals of active/inactive time, redirect count, and the last 200
  checks.

## Setup

1. Push this folder to a new GitHub repo.
2. Edit `hosts.json` with the hosts you want the scheduled checker to track.
3. Actions are enabled by default on most repos — the workflow will start
   running on its cron schedule, or trigger it manually from the Actions tab
   (`workflow_dispatch`).
4. Host `index.html` however you like (GitHub Pages, any static host, or just
   open it locally) for the live dashboard.
5. Optional: point the dashboard's Settings → Backend URL at a small proxy you
   control that returns `{status, ok, responseTimeMs, redirected, finalUrl}`
   for a given `?url=` — that gets you real status codes and redirect info in
   the live view, not just reachable/unreachable.

## Notes

- The live dashboard's per-session metrics (in the browser) are separate from
  `status-history.json` (committed by the Action) — the former is instant and
  local, the latter is the durable, git-tracked record.
- `check_status.py` estimates active/inactive time as the gap between
  scheduled runs, so shorten the cron interval for finer-grained metrics.
