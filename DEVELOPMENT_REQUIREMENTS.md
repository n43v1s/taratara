# Development Requirements

Status snapshot: 2026-06-27, local workspace `D:\Projects\Gyanna\tara-caraka-ceria`.

Legend:

- `[OK]` = available and matches the recommended project baseline.
- `[X]` = missing, not installed, or not yet present in this project.
- `[INFO]` = informational or optional for the first version.

## Confirmed Local Environment

| Component | Recommended baseline | Local check result | Status | Notes |
| --- | --- | --- | --- | --- |
| Python | `3.14.x` stable bugfix branch | `Python 3.14.6` | `[OK]` | Active through both `py --version` and `python --version`. |
| pip | `26.1.2` | `pip 26.1.2` for Python 3.14 | `[OK]` | Used to install Python dependencies. |
| FastAPI | `0.138.1` | Installed in `.venv` | `[OK]` | Install inside project virtual environment. |
| Jinja2 | `3.1.6` | Installed in `.venv` | `[OK]` | Install inside project virtual environment. |
| HTMX | `2.0.10` | `app/static/vendor/htmx.min.js` present | `[OK]` | Vendored under `static/vendor/`. |
| JavaScript | Vanilla browser JavaScript | Minimal inline JS only | `[OK]` | JavaScript has no LTS concept like Node.js; use modern browser-safe vanilla JS only when needed. |
| Node.js | Optional, `24.18.0` LTS if npm tooling is needed | `v24.18.0` | `[OK]` | Not required for the first FastAPI + Jinja2 + HTMX version unless using npm tooling. |
| npm | Optional, bundled with Node.js | `11.16.0` via `npm.cmd` | `[OK]` | Plain `npm` in PowerShell is blocked by execution policy; use `npm.cmd` or adjust policy later. |
| PowerShell | Windows PowerShell available for scheduler script | `5.1.26100.8655` | `[OK]` | Needed to run `tara-caraka-form.ps1`. |
| cloudflared | Installed Cloudflare Tunnel client | `2026.6.1` | `[OK]` | Needed when exposing the local panel through Cloudflare Tunnel. |

## Recommended Stack Baseline

Use these versions as the initial development baseline unless a later compatibility check changes them.

| Stack item | Version / policy | Role in this project |
| --- | --- | --- |
| Python | `3.14.6` | Backend runtime for FastAPI, parsing, JSON handling, fuzzy matching, and launching PowerShell. |
| pip | `26.1.2` | Python package installer. Do not add pip as an app runtime dependency. |
| FastAPI | `0.138.1` | Backend web framework for routes, validation, status endpoints, dry-run, and submit orchestration. |
| Jinja2 | `3.1.6` | Server-rendered HTML templates for dashboard, forms, mapping review, config editor, and logs. |
| HTMX | `2.0.10` | Lightweight HTML-driven interactions without a React frontend. |
| JavaScript | Vanilla browser JavaScript | Small UI behavior only where HTMX or HTML forms are not enough. |
| Node.js | `24.18.0` LTS, optional | Only needed if using npm to fetch frontend assets or add build tooling later. |

## Python Dependencies

| Package | Purpose | Status |
| --- | --- | --- |
| `fastapi==0.138.1` | Web framework | `[OK]` |
| `jinja2==3.1.6` | HTML templates | `[OK]` |
| `uvicorn` | Local ASGI server for FastAPI | `[OK]` |
| `httpx` | Fetch Google Form HTML and perform HTTP requests | `[OK]` |
| `beautifulsoup4` | Parse Google Form HTML | `[OK]` |
| `rapidfuzz` | Fuzzy matching for changed or mistyped Google Form labels | `[OK]` |
| `python-multipart` | Form submission support for FastAPI | `[OK]` |

## Project Components

| Component | Role | Expected implementation area | Status |
| --- | --- | --- | --- |
| FastAPI web application | Main backend control panel | `app/main.py`, routers, services | `[OK]` |
| Dashboard | Show current flow state and main actions | `app/routers/dashboard.py` + `dashboard.html` | `[OK]` |
| Flow diagram | 5-step visual workflow indicator on dashboard | `app/services/flow_state.py` + `dashboard.html` | `[OK]` |
| Session concept | Group runs by `sessionId` generated at parse time; allows multiple booking cycles | `form-profile.json`, run records, flow_state.py | `[OK]` |
| Help / guide page | Explain workflow and safety rules | Route + template | `[X]` |
| Google Form parser | Fetch and parse form ID, response URL, field labels, entry IDs, options, and booking dates | `app/services/form_parser.py` | `[OK]` |
| Field matching service | Match parsed Google Form labels to stable internal fields | `app/services/field_matcher.py` using aliases and rapidfuzz | `[OK]` |
| Field mapping review | Let user accept or correct suggested field mappings | `app/routers/mapping.py` + `mapping.html` | `[OK]` |
| Config editor | Edit default answer values; shows dropdowns/radios from real form options | `app/routers/config.py` + `config.html` | `[OK]` |
| Config invalidation tracking | `configUpdatedAt` timestamp saved when payload fields change; dryrun required after each config save | `app/services/config_handler.py` | `[OK]` |
| Booking date selector | Select booking dates from parsed form options | Part of config editor | `[OK]` |
| Dry-run flow | Run scheduler in dry-run mode and show report/log | `app/routers/dryrun.py` + `dryrun.html` | `[OK]` |
| Dry-run result page | View saved dry-run result via `GET /dryrun/result/{run_id}` | `app/routers/dryrun.py` | `[OK]` |
| Dry-run re-run button | "↺ Dry Run Ulang" button on result page | `dryrun.html` | `[OK]` |
| Prepare submit flow | Build final submission summary before confirmation | `app/routers/submit.py` + `submit_prepare.html` | `[OK]` |
| Confirm submit flow | Start real background scheduler after explicit confirmation | `app/routers/submit.py` + `submit_confirm.html` | `[OK]` |
| Scheduler runner | Launch and monitor `tara-caraka-form.ps1` safely | `app/services/scheduler_runner.py` | `[OK]` |
| Scheduler lock handling | Prevent duplicate active submit runs; PS writes its own lock | `tara-caraka-form.ps1` + `data/scheduler.lock` | `[OK]` |
| Scheduler status view | Show active/inactive state and log tail | `app/routers/status.py` + `status.html` | `[OK]` |
| Logs and run history | Audit dry-runs, submits, failures; grouped by session | `app/routers/logs.py` + `logs.html` | `[OK]` |
| Live log fragment polling | HTMX polling for active run logs via `GET /logs/{run_id}/fragment` | `app/routers/logs.py` + `log_fragment.html` | `[OK]` |
| Validation layer | Block submit when config, mapping, or dryrun are incomplete | `app/services/validator.py` | `[OK]` |
| Reset page | Clear form data, run history, and/or scheduler lock | `app/routers/reset.py` + `reset.html` | `[OK]` |
| Developer test submit card | Force-schedule a submit N seconds from now; configurable delay | Dashboard card → `POST /submit/test` | `[OK]` |
| "Mulai Sesi Baru" button | Shown on dashboard after successful submit; clears form to start a new booking cycle | `dashboard.html` → `POST /reset/form` | `[OK]` |
| Cloudflare Tunnel exposure notes | Document local-to-public tunnel setup assumptions | `CLAUDE.md` + `README.md` | `[OK]` |
| Test suite | Verify parser, matching, config validation, and safety behavior | `tests/` | `[X]` |

## Project Files And Directories

| File / directory | Purpose | Status |
| --- | --- | --- |
| `README.md` | Project decision and architecture notes | `[OK]` |
| `DEVELOPMENT_REQUIREMENTS.md` | Development baseline and environment checklist | `[OK]` |
| `CLAUDE.md` | Claude implementation agent instructions | `[OK]` |
| `.git/` | Git repository metadata | `[OK]` |
| `.gitignore` | Ignore local env, caches, logs, and generated files | `[OK]` |
| `.venv/` | Project-specific Python virtual environment | `[OK]` |
| `requirements.txt` | Python dependency declaration | `[OK]` |
| `.env.example` | Example environment variables | `[OK]` |
| `scripts/dev.ps1` | Local development startup helper | `[OK]` |
| `app/` | Main application package | `[OK]` |
| `app/main.py` | FastAPI app entrypoint | `[OK]` |
| `app/routers/dashboard.py` | Dashboard route | `[OK]` |
| `app/routers/form.py` | Google Form URL input and parse trigger | `[OK]` |
| `app/routers/mapping.py` | Field mapping review | `[OK]` |
| `app/routers/config.py` | Config editor | `[OK]` |
| `app/routers/dryrun.py` | Dry-run execution and result view | `[OK]` |
| `app/routers/submit.py` | Prepare submit, confirm submit, test submit | `[OK]` |
| `app/routers/status.py` | Scheduler status view | `[OK]` |
| `app/routers/logs.py` | Run history and live log fragment | `[OK]` |
| `app/routers/reset.py` | Reset form, runs, and lock | `[OK]` |
| `app/services/form_parser.py` | Google Form fetch and parse | `[OK]` |
| `app/services/field_matcher.py` | Alias and fuzzy field matching | `[OK]` |
| `app/services/config_handler.py` | Config read/write with `configUpdatedAt` tracking | `[OK]` |
| `app/services/flow_state.py` | 5-step flow state derived from config + runs | `[OK]` |
| `app/services/scheduler_runner.py` | Launch PowerShell, read runs and logs (utf-8-sig aware) | `[OK]` |
| `app/services/validator.py` | Pre-flight checks including dryrun-after-config validation | `[OK]` |
| `app/templates/base.html` | Base layout with navbar | `[OK]` |
| `app/templates/dashboard.html` | Dashboard with flow diagram, session banner, developer card | `[OK]` |
| `app/templates/form.html` | Form URL input and parse result | `[OK]` |
| `app/templates/mapping.html` | Field mapping review table | `[OK]` |
| `app/templates/config.html` | Config editor with form-driven dropdowns and checkboxes | `[OK]` |
| `app/templates/dryrun.html` | Dry-run result with payload preview, log, and re-run button | `[OK]` |
| `app/templates/submit_prepare.html` | Submit summary with edit links | `[OK]` |
| `app/templates/submit_confirm.html` | Confirm submit page | `[OK]` |
| `app/templates/status.html` | Scheduler status page | `[OK]` |
| `app/templates/logs.html` | Run history grouped by session | `[OK]` |
| `app/templates/log_fragment.html` | HTMX polling fragment for live log updates | `[OK]` |
| `app/templates/reset.html` | Reset page | `[OK]` |
| `app/templates/test_submit_result.html` | HTMX fragment for test submit result + live log | `[OK]` |
| `app/static/vendor/htmx.min.js` | Vendored HTMX `2.0.10` | `[OK]` |
| `app/static/css/` | CSS stylesheets | `[OK]` |
| `data/tara-caraka-form.config.json` | Default answer values keyed by stable internal field names | `[OK]` |
| `data/form-profile.json` | Parsed Google Form metadata, confirmed mappings, and `sessionId` | `[OK]` |
| `data/field-aliases.json` | Known label variations for each internal field | `[OK]` |
| `data/runs/` | Run history records (one JSON per run) | `[OK]` |
| `data/logs/` | Log files (one `.log` per run) | `[OK]` |
| `data/scheduler.lock` | Active scheduler lock (runtime, not committed) | `[OK]` |
| `tara-caraka-form.ps1` | PowerShell scheduler submit script; writes runs, logs, and lock without BOM | `[OK]` |
| `tests/` | Automated tests | `[X]` |

## Notes

- PowerShell 5.1 `Set-Content -Encoding UTF8` writes a UTF-8 BOM. The project uses `[System.IO.File]::WriteAllText` with `UTF8` encoding (no BOM) to avoid this. Python reads all run and log files with `utf-8-sig` to handle both cases.
- The scheduler lock is written by `tara-caraka-form.ps1` after it starts, not by FastAPI, to avoid a race condition where FastAPI wrote the lock before PS checked it.
- `configUpdatedAt` is saved to config whenever a payload field value changes. Dry-run is only considered valid if its `startedAt` timestamp is ≥ `configUpdatedAt`. Changing only `attemptTimes` does not update the timestamp.
- The session concept uses `sessionId` (UUID) and `sessionLabel` (human-readable date) stored in `form-profile.json` at parse time and copied into each run record. This allows log grouping and flow state filtering per booking cycle.
- Google Forms closes the connection after receiving a form POST (not an error). The PowerShell script detects this by matching connection-closed error messages and treats them as success.
- PowerShell is launched with `-NoExit` so the terminal stays open after the script finishes, allowing the user to inspect errors.
- The real submit path must remain in the background PowerShell scheduler, not in a long-running HTTP request.
- Avoid relying on globally installed Python packages. Use `.venv` for repeatable development.
