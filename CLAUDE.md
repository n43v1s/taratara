# CLAUDE.md — Tara Caraka Ceria

This file is read by Claude Code at the start of every session.
Keep it up to date as the project evolves.

---

## What This Project Is

A **local web control panel** for automating pediatric health-check booking via Google Forms.

- Runs on the owner's laptop only.
- Exposed publicly through Cloudflare Tunnel + Cloudflare Access when needed.
- The primary interface is a FastAPI web panel, not a bot.
- The actual timed form submission is handled by a background PowerShell script (`tara-caraka-form.ps1`), not a long-running HTTP request.

Full architecture, product scope, and use-case specs are in `README.md`.
Environment baseline and component checklist are in `DEVELOPMENT_REQUIREMENTS.md`.

---

## Tech Stack

| Layer | Choice | Version |
|---|---|---|
| Backend | Python + FastAPI | Python 3.14.6 / FastAPI 0.138.1 |
| Templates | Jinja2 | 3.1.6 |
| Frontend interactions | HTMX (vendored) | 2.0.10 |
| Frontend scripting | Vanilla browser JS | — |
| Local ASGI server | Uvicorn | latest |
| Form parsing | httpx + BeautifulSoup4 | latest |
| Fuzzy field matching | rapidfuzz | latest |
| Submit scheduler | PowerShell 5.1 | system |
| Tunnel | cloudflared | 2026.6.1 |

Do **not** introduce React, Vue, or a separate frontend build unless explicitly decided.
Do **not** use globally installed Python packages — always use `.venv`.

---

## Project Layout

```
tara-caraka-ceria/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── routers/
│   │   ├── dashboard.py     # Dashboard + flow state
│   │   ├── form.py          # Google Form URL input and parse trigger
│   │   ├── mapping.py       # Field mapping review
│   │   ├── config.py        # Config editor (with form-driven dropdowns)
│   │   ├── dryrun.py        # Dry-run execution and result view
│   │   ├── submit.py        # Prepare submit, confirm submit, test submit
│   │   ├── status.py        # Scheduler status view
│   │   ├── logs.py          # Run history and live log fragment
│   │   └── reset.py         # Reset form data, runs, scheduler lock
│   ├── services/
│   │   ├── form_parser.py       # Google Form fetch and parse
│   │   ├── field_matcher.py     # Alias and fuzzy field matching
│   │   ├── config_handler.py    # Config read/write with configUpdatedAt tracking
│   │   ├── flow_state.py        # 5-step flow state derived from config + runs
│   │   ├── scheduler_runner.py  # Launch PS, read runs and logs (utf-8-sig)
│   │   └── validator.py         # Pre-flight checks including dryrun-after-config
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html       # Flow diagram, session banner, developer test card
│   │   ├── form.html
│   │   ├── mapping.html
│   │   ├── config.html          # Config editor with form-driven dropdowns/checkboxes
│   │   ├── dryrun.html          # Dry-run result with payload preview and re-run button
│   │   ├── submit_prepare.html  # Submit summary with edit links
│   │   ├── submit_confirm.html
│   │   ├── status.html
│   │   ├── logs.html            # Run history grouped by session
│   │   ├── log_fragment.html    # HTMX polling fragment for live log updates
│   │   ├── reset.html
│   │   └── test_submit_result.html  # HTMX fragment for test submit result + live log
│   └── static/
│       ├── vendor/
│       │   └── htmx.min.js  # Vendored HTMX 2.0.10
│       └── css/
├── data/
│   ├── tara-caraka-form.config.json   # Default form answer values + configUpdatedAt
│   ├── form-profile.json              # Parsed Google Form metadata + confirmed mappings + sessionId
│   ├── field-aliases.json             # Known label variations per internal field
│   ├── runs/                          # Per-run JSON records
│   ├── logs/                          # Per-run log files
│   └── scheduler.lock                 # Active scheduler lock (runtime, not committed)
├── tests/
├── tara-caraka-form.ps1    # PowerShell background scheduler (submit path)
├── scripts/
│   └── dev.ps1             # Local dev startup helper
├── requirements.txt         # Pinned Python dependencies
├── .venv/                   # Project virtual environment (not committed)
├── .env.example             # Example env vars
├── .gitignore
├── CLAUDE.md                # This file
├── README.md                # Architecture and design decisions
└── DEVELOPMENT_REQUIREMENTS.md
```

---

## Development Commands

All commands assume the project virtual environment is active.

### First-time setup

```powershell
# Create venv
py -3.14 -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Run the dev server

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Run tests

```powershell
pytest tests/ -v
```

### Vendor HTMX (one-time)

```powershell
# Download htmx.min.js 2.0.10 into static/vendor/
Invoke-WebRequest -Uri "https://unpkg.com/htmx.org@2.0.10/dist/htmx.min.js" -OutFile "app/static/vendor/htmx.min.js"
```

---

## Stable Internal Fields

These field names are stable across Google Form changes. Always map form labels to these:

| Internal field | Meaning |
|---|---|
| `childName` | Child's name |
| `birthInfo` | Birth date / birth info |
| `childAge` | Child's age |
| `gender` | Gender |
| `religion` | Religion |
| `parentName` | Parent/guardian name |
| `satker` | Work unit (satker) |
| `phoneNumber` | Contact phone number |
| `address` | Address |
| `allergy` | Allergy information |
| `bookingDates` | Selected booking dates |

---

## Field Matching Rules

Match parsed Google Form labels to internal fields using three layers in order:
1. Exact match or alias match (from `data/field-aliases.json`)
2. Fuzzy match with `rapidfuzz`
3. Manual review by the user

Confidence policy:
- ≥ 90%: auto-map, but show in review
- 75–89%: suggest and require user confirmation
- < 75%: mark unmapped, require manual selection

**Never auto-submit when mapping is uncertain. Block dry-run and submit until required fields are confirmed.**

---

## Data File Contracts

`tara-caraka-form.config.json` — default answer values keyed by stable internal field names, plus `configUpdatedAt` (ISO timestamp, updated when any payload field value changes).

`form-profile.json` — live Google Form metadata: form ID, response URL, all detected fields with `entry.*` IDs, options, confirmed field mappings, `sessionId`, and `sessionLabel`.

`field-aliases.json` — array of known label variants per internal field (for alias matching before fuzzy).

These files are **separate on purpose**: form metadata changes when a new form is issued; default values change only when the user edits config.

---

## Session Concept

Each time a new Google Form is parsed, a `sessionId` (UUID) and `sessionLabel` (human-readable date string) are written to `form-profile.json`. Every run record carries the `sessionId` of the session it belongs to.

- The flow diagram on the dashboard filters runs by the current session.
- Logs are grouped by session on the `/logs` page.
- "Mulai Sesi Baru" on the dashboard clears `form-profile.json` to start a new booking cycle.

---

## Config Invalidation (`configUpdatedAt`)

When the user saves config and any **payload field** value changes (`childName`, `birthInfo`, `childAge`, `gender`, `religion`, `parentName`, `satker`, `phoneNumber`, `address`, `allergy`, `bookingDates`), `config_handler.save_config()` writes `configUpdatedAt` with the current UTC ISO timestamp.

A dry-run is only considered valid if its `startedAt` >= `configUpdatedAt`. Changing only `attemptTimes` does **not** update `configUpdatedAt` because it does not affect the submitted payload.

---

## Submit / Scheduler Safety Rules

These rules must be respected in every implementation decision:

1. **Submit requires explicit user confirmation** — no automatic or implicit submit.
2. **The PowerShell scheduler writes its own lock file** after it starts — FastAPI must not write the lock file, to avoid a race condition where FastAPI writes the lock before PS checks it.
3. **FastAPI must not hold an HTTP request open** while waiting for the submit time window.
4. **The PowerShell scheduler** (`tara-caraka-form.ps1`) handles the actual timed submit — FastAPI only starts it as a background process.
5. **Log every dry-run and submit attempt**, including errors.
6. **Prevent laptop sleep** during the submit scheduler window.
7. **Never expose raw shell command execution** in the web UI — only predefined actions (parse, dry-run, prepare-submit, confirm-submit, cancel, status, test-submit).
8. **Avoid arbitrary user input reaching shell execution** — validate and whitelist all parameters.
9. **Launch PowerShell with `-NoExit`** so the terminal stays open for debugging after the script finishes or errors.

---

## PowerShell / Python Encoding Notes

- PowerShell 5.1 `Set-Content -Encoding UTF8` writes a UTF-8 BOM. The project uses `[System.IO.File]::WriteAllText(path, content, [System.Text.Encoding]::UTF8)` instead (no BOM).
- Python reads all run and log files with `encoding="utf-8-sig"` to handle both BOM and non-BOM files gracefully.
- All non-ASCII characters (`—`, etc.) in `tara-caraka-form.ps1` must be replaced with ASCII equivalents to avoid corruption when PowerShell reads the file in different encodings.

---

## Cloudflare Access

The web panel is protected by Cloudflare Access. Only `agusrokyanto@gmail.com` and one sibling email are allowed.
The app itself does not implement authentication — it relies entirely on Cloudflare Access upstream.

---

## Scope Batasan (Baca Ini Dulu)

Claude hanya bekerja di **local environment**. Jangan menyentuh, mengkonfigurasi,
atau menjalankan apapun yang berkaitan dengan:

- Cloudflare Tunnel (`cloudflared`)
- Domain `tara.agusrokyanto.com`
- Cloudflare Access rules
- DNS atau public exposure apapun

Semua testing dan development dilakukan di `http://127.0.0.1:8000` saja.
Jika ada fitur yang tampaknya memerlukan public URL, implementasikan dulu untuk local,
lalu tandai dengan komentar `# TODO: expose via Cloudflare Tunnel`.

---

## What Is Not Yet Built

Check `DEVELOPMENT_REQUIREMENTS.md` for the full component and file checklist.
Anything marked `[X]` is not yet implemented. Currently the only remaining gap is the test suite (`tests/`).
