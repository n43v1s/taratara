#  Tara Local Web Control Panel

## Decision

Build a custom local web control panel instead of using WhatsApp, Discord, Telegram, or n8n as the primary command interface.

The web app will run only on the local laptop and will be exposed through Cloudflare Tunnel when needed.

## Target Architecture

```text
User / authorized family member
-> Cloudflare Access login
-> tara.agusrokyanto.com
-> Cloudflare Tunnel
-> local web service on laptop
-> tara-caraka-form.ps1 scheduler automation
```

## Access Model

- Use a dedicated subdomain such as `tara.agusrokyanto.com`.
- Protect the web UI with Cloudflare Access.
- Allow only the owner's email and the sibling's email.
- The service is only reachable while the laptop, local web service, and Cloudflare Tunnel are running.

## Product Scope

The web control panel should support:

- Help page / command guide.
- View current config/default values.
- Submit a Google Form URL.
- Fetch and parse Google Form metadata:
  - Form ID
  - Response URL
  - field names
  - `entry.*` field IDs
  - available booking date options
- Dynamically map parsed Google Form fields to stable internal fields.
- Detect likely field matches even when labels have typo or wording variations.
- Let the user review and manually correct field mapping before dry-run/submit.
- Edit config/default values.
- Select booking dates.
- Run dry-run without submitting.
- Show dry-run report/log.
- Prepare submit with summary.
- Require explicit confirmation before real submit.
- Execute the scheduler submit. Ubuntu uses the Python scheduler; Windows can keep using the legacy PowerShell script if needed.
- Show scheduler status and latest logs.

## Tech Stack Decision

Final stack for the first version:

```text
Python FastAPI
+ Jinja2 server-rendered HTML
+ HTMX or small vanilla JavaScript
+ simple CSS / lightweight UI styling
+ JSON files for config, form profiles, run history, and logs
+ background scheduler runner
```

Reasons:

- The app is a local control panel, not a complex public frontend.
- It still needs a backend to update config, parse Google Forms, read logs, and execute the scheduler.
- React is not required for the first version because most screens are forms, tables, buttons, confirmations, and log views.
- Avoiding React keeps the project smaller: no separate frontend build, fewer dependencies, fewer moving parts, and simpler debugging.
- Python is a good fit for HTML parsing, JSON handling, fuzzy matching, and launching PowerShell on Windows.
- FastAPI has a smaller runtime footprint than Spring Boot and is preferred for this laptop-local automation.
- The web app must act as a control panel, not as the timing-critical submit loop.

Possible later alternatives:

- Java Spring Boot + Thymeleaf is valid if the project needs a more Java-oriented structure.
- React can be added later if the UI becomes much more interactive.
- n8n can remain a supporting tool, but it is not the primary interface for this automation.

## Ubuntu Local Setup

The original scheduler was written for Windows PowerShell. On Ubuntu, use the
Python scheduler entrypoint instead; the FastAPI routes launch
`python -m app.scheduler_cli` for dry-run, test submit, and real submit.

Install the OS venv package first if Python does not include `ensurepip`:

```bash
sudo apt install python3.14-venv
```

Then set up and start the project:

```bash
./scripts/setup_ubuntu.sh
./scripts/start_ubuntu.sh
```

The server starts at `http://127.0.0.1:8000` by default. Runtime JSON files are
created from `data/*.example.json` when missing, while run history and logs live
under `data/runs/` and `data/logs/`.

## Background Scheduler Execution Model

Real submit timing is handled by a background scheduler process, not by a long-running browser request.

Implemented execution model:

```text
User clicks Confirm Submit
-> FastAPI validates config, mapping, dry-run status (no active scheduler lock)
-> FastAPI starts the scheduler as a background process
-> FastAPI immediately returns "scheduler started"
-> Scheduler writes its own lock file after starting
-> Scheduler process waits for configured submit times
-> Scheduler sends submit attempts at configured times
-> Scheduler writes run record and log file
-> FastAPI reads logs/status for the UI
```

Important implementation notes:

- FastAPI does not write the scheduler lock file — PowerShell writes it after it starts. This avoids a race condition where FastAPI writes the lock before PS starts, causing PS to detect its own lock and abort.
- Google Forms closes the HTTP connection after receiving a POST — this is expected behavior. The script detects connection-closed errors and treats them as success.
- PowerShell is launched with `-NoExit` so the terminal stays open for debugging after the script finishes or errors.
- PowerShell 5.1 `Set-Content -Encoding UTF8` writes a UTF-8 BOM. The project uses `[System.IO.File]::WriteAllText` with `UTF8` encoding instead. Python reads run/log files with `utf-8-sig` to handle both formats gracefully.
- Submit-time work is minimal: build payload from saved config/profile, send requests, and write concise logs.
- The laptop must be prevented from sleeping during the scheduler window.

## Dynamic Form Handling

Google Form structure must be treated as dynamic. Field labels, `entry.*` IDs, options, and booking dates can change between forms or over time.

The automation must not depend on hardcoded field IDs inside the main script.

Preferred flow:

```text
Google Form URL
-> parse live form metadata
-> extract form ID, response URL, field labels, entry IDs, field types, and options
-> map parsed fields to stable internal fields
-> show mapping review in the web UI
-> let user accept or fix mappings
-> save form profile
-> run dry-run
-> require explicit confirmation
-> execute submit scheduler
```

Stable internal fields should remain consistent even when Google Form labels change:

```text
childName
birthInfo
childAge
gender
religion
parentName
satker
phoneNumber
address
allergy
bookingDates
```

Dynamic Google Form metadata should be saved separately from default answer values.

Recommended data files:

```text
data/tara-caraka-form.config.json
data/form-profile.json
data/field-aliases.json
data/runs/
data/logs/
```

`tara-caraka-form.config.json` stores default answer values.

`form-profile.json` stores parsed form metadata and confirmed field mappings.

`field-aliases.json` stores known label variations for each internal field.

## Field Matching Strategy

Field detection should use three layers:

```text
1. Exact and alias matching
2. Fuzzy matching
3. Manual review and correction
```

Example aliases:

```json
{
  "parentName": [
    "Nama Orang Tua",
    "Nama Orangtua",
    "Nama Ortu",
    "Nama Wali",
    "NAMA ORAGTUA"
  ],
  "bookingDates": [
    "Tanggal Booking",
    "Tanggal",
    "Pilih Tanggal",
    "Tanggal Kedatangan"
  ]
}
```

Before matching, labels should be normalized:

```text
trim spaces
lowercase
remove repeated whitespace
ignore punctuation differences
optionally normalize common abbreviations such as "ortu" -> "orang tua"
```

Typo handling should use fuzzy matching, for example with Python `rapidfuzz`.

Suggested confidence policy:

| Confidence | Behavior |
| --- | --- |
| `>= 90%` | Auto-map but still show in review. |
| `75-89%` | Suggest match and require user confirmation. |
| `< 75%` | Mark as unmapped and require manual selection. |

Example:

```text
Internal field: parentName
Detected label: NAMA ORAGTUA
Suggested match: Nama Orang Tua
Confidence: medium/high
Status: Needs confirmation unless the score is above the auto-map threshold
```

Important safety rule:

```text
When field mapping is uncertain, the system must stop and ask for review.
It must not guess and submit.
```

## Bot Commands vs Web Features

The earlier bot command plan is preserved as a feature map for the web UI.

| Planned bot command | Web control panel feature | Notes |
| --- | --- | --- |
| `/help` | Help / guide page | Show available actions, workflow, and safety notes. |
| `/example` | Example flow page or inline examples | Show a sample form setup, dry-run, and submit confirmation flow. |
| `/form <url>` | Form URL input + Parse Form button | Fetch Google Form metadata and detect Form ID, response URL, fields, and date options. |
| `/fields` | Fields table | Show field names, entry IDs, detected options, and current default values. |
| `/set key=value` | Config editor form | Update default values through controlled inputs instead of free-form commands. |
| `/dates` | Available booking dates section | Show all booking date options parsed from the current Google Form. |
| `/book <date1,date2>` | Booking date multi-select | Choose one or more parsed booking dates with checkboxes. |
| `/dryrun` | Dry Run button | Runs `tara-caraka-form.ps1 -TestDryRun`; never submits. |
| `/submit` | Prepare Submit button | Builds a summary and creates a pending confirmation, but does not submit yet. |
| `/confirm <run_id>` | Confirm Submit button | Executes scheduler submit only after explicit confirmation. |
| `/status` | Status panel | Shows active scheduler state, latest run ID, and latest log tail. |
| `/cancel` | Cancel scheduler button | Cancels an active scheduler only when it is safe and before scheduled submit attempts fire. |

The web UI should prefer buttons, forms, tables, checkboxes, and confirmation dialogs over raw command text. This reduces parsing ambiguity and makes risky actions easier to review before execution.

## Use Cases

### UC-01: Open Control Panel

**Actor:** Authorized user.

**Goal:** Access the local automation panel securely.

**Preconditions:**

- Laptop is on.
- Cloudflare Tunnel is healthy.
- Local web service is running.
- User email is allowed by Cloudflare Access.

**Main flow:**

1. User opens `https://tara.agusrokyanto.com`.
2. Cloudflare Access asks the user to authenticate.
3. User authenticates with an allowed email.
4. Web app shows dashboard, current status, and available actions.

**Alternative / error flow:**

- If local service is off, Cloudflare shows an origin/tunnel error.
- If user email is not allowed, Cloudflare Access denies access.

### UC-02: View Help and Example Flow

**Actor:** Authorized user.

**Goal:** Understand how to use the automation panel safely.

**Main flow:**

1. User opens Help or Example page.
2. Web app shows the normal flow:
   - parse form
   - review fields
   - update config
   - choose booking dates
   - dry-run
   - prepare submit
   - confirm submit
   - monitor status
3. Web app highlights that dry-run never submits and real submit requires confirmation.

### UC-03: Parse Google Form URL

**Actor:** Authorized user.

**Goal:** Load a new Google Form and detect the fields needed for automation.

**Preconditions:**

- User has a Google Form URL.
- Laptop has internet access.

**Main flow:**

1. User enters Google Form URL.
2. User clicks Parse Form.
3. Web app fetches the form HTML.
4. Web app extracts:
   - form ID
   - response URL
   - field names
   - `entry.*` IDs
   - field options
   - booking date options
   - current `fbzx` fallback value when available
5. Web app saves parsed metadata into config.
6. Web app shows detected fields and date options for review.

**Alternative / error flow:**

- If URL is invalid, show validation error.
- If form cannot be fetched, show network error.
- If required fields cannot be detected, show which fields are missing and block submit.

### UC-04: Review Fields and Defaults

**Actor:** Authorized user.

**Goal:** Confirm that detected fields match the intended form.

**Main flow:**

1. User opens Fields page/table.
2. Web app displays each field:
   - label
   - entry ID
   - type
   - options, if any
   - current default value
3. User checks whether values are correct before running dry-run.

**Alternative / error flow:**

- If a field has no mapping/default value, web app marks it as incomplete.
- If booking date options are empty, web app blocks submit until fixed.

### UC-05: Update Config Values

**Actor:** Authorized user.

**Goal:** Change form answer defaults without editing PowerShell code.

**Main flow:**

1. User opens Config Editor.
2. User updates fields such as child name, birth info, age, gender, religion, parent name, satker, phone, address, allergy, and booking dates.
3. User saves config.
4. Web app validates the config.
5. Web app writes changes to `tara-caraka-form.config.json`.

**Alternative / error flow:**

- If required values are missing, web app shows field-level errors.
- If a selected booking date is not available in the parsed form, web app rejects it.

### UC-06: Select Booking Dates

**Actor:** Authorized user.

**Goal:** Choose booking dates from detected Google Form options.

**Main flow:**

1. User opens booking date section.
2. Web app shows available dates as checkboxes.
3. User selects one or more dates.
4. User saves selection.
5. Web app stores selected dates in config.

**Alternative / error flow:**

- If no dates are selected, web app blocks dry-run/submit.
- If the form is re-parsed and selected dates no longer exist, web app asks user to reselect dates.

### UC-07: Run Dry-Run

**Actor:** Authorized user.

**Goal:** Test the payload and schedule without submitting the Google Form.

**Preconditions:**

- Config is valid.
- Required field mappings exist.

**Main flow:**

1. User clicks Dry Run.
2. Web app runs:
   - `tara-caraka-form.ps1 -TestDryRun`
3. PowerShell script builds payload and scheduled attempts.
4. Script does not submit to Google Form.
5. Web app shows dry-run report:
   - run ID
   - form endpoint
   - field values
   - selected booking dates
   - scheduled attempt times
   - payload preview when enabled

**Alternative / error flow:**

- If script exits with error, web app shows stderr/log tail.
- If config is invalid, web app blocks dry-run and shows missing items.

### UC-08: Prepare Submit

**Actor:** Authorized user.

**Goal:** Review final submission summary before scheduling real submit.

**Preconditions:**

- Dry-run has completed successfully, or user explicitly accepts running submit without recent dry-run.
- Config is valid.

**Main flow:**

1. User clicks Prepare Submit.
2. Web app creates a pending submit run.
3. Web app shows summary:
   - form URL
   - response URL
   - child name
   - selected field values
   - selected booking dates
   - scheduled times
4. Web app shows Confirm Submit button.

**Alternative / error flow:**

- If another scheduler is active, web app refuses to create a new pending submit.
- If config changed after dry-run, web app asks user to run dry-run again.

### UC-09: Confirm and Execute Scheduler Submit

**Actor:** Authorized user.

**Goal:** Start the real scheduled Google Form submit attempts.

**Preconditions:**

- Pending submit exists.
- No active scheduler lock exists.

**Main flow:**

1. User clicks Confirm Submit.
2. Web app creates scheduler lock.
3. Web app starts PowerShell submit process:
   - `tara-caraka-form.ps1 -Mode Submit`
4. Script fetches live form metadata.
5. Script queues async submit attempts at configured scheduled times.
6. Web app shows scheduler started status and run ID.

**Alternative / error flow:**

- If scheduler lock exists, web app blocks duplicate submit.
- If live form metadata fetch fails, web app logs the error and marks submit as failed.
- If process cannot start, web app clears pending submit but preserves error logs.

### UC-10: Monitor Scheduler Status

**Actor:** Authorized user.

**Goal:** See whether scheduler is waiting, submitted, failed, or finished.

**Main flow:**

1. User opens Status page.
2. Web app reads active lock, process state, and latest log.
3. Web app displays:
   - active/inactive state
   - run ID
   - process ID, if available
   - next scheduled attempt
   - latest log lines
   - HTTP results when available

**Alternative / error flow:**

- If process ended but lock remains, web app marks stale lock and offers cleanup.
- If log cannot be read due to file lock, web app retries or shows last known status.

### UC-11: Cancel Scheduler

**Actor:** Authorized user.

**Goal:** Stop a scheduler before real submit attempts fire.

**Preconditions:**

- Scheduler is active.
- Current time is before the first scheduled submit attempt.

**Main flow:**

1. User clicks Cancel Scheduler.
2. Web app checks whether submit attempts have already started.
3. If safe, web app stops scheduler process.
4. Web app clears scheduler lock.
5. Web app logs cancellation.

**Alternative / error flow:**

- If attempts may already have fired, web app refuses automatic cancellation and shows warning.
- If process cannot be stopped, web app shows manual recovery instructions.

### UC-12: View Logs and Run History

**Actor:** Authorized user.

**Goal:** Audit dry-run, submit, errors, and cancellations.

**Main flow:**

1. User opens Logs or History page.
2. Web app shows recent runs:
   - run ID
   - mode
   - timestamp
   - config snapshot hash or version
   - status
   - log file link/preview
3. User opens a run to inspect details.

**Alternative / error flow:**

- If log file is missing, web app marks the run as incomplete and shows available metadata.

### UC-13: Handle Changed or Mistyped Form Fields

**Actor:** Authorized user.

**Goal:** Safely continue automation even when the Google Form uses changed labels, new field IDs, different wording, or typo such as `NAMA ORAGTUA`.

**Preconditions:**

- User has entered a Google Form URL.
- Web app can fetch and parse the form.

**Main flow:**

1. User clicks Parse Form.
2. Web app extracts all visible field labels, `entry.*` IDs, field types, and options.
3. Web app normalizes field labels before matching.
4. Web app compares parsed labels against known aliases and fuzzy matches.
5. Web app classifies mapping confidence:
   - high confidence
   - medium confidence
   - low confidence / unmapped
6. Web app shows a mapping review page.
7. User accepts suggested mappings or manually chooses the correct parsed field.
8. Web app saves confirmed mapping into `form-profile.json`.
9. Web app allows dry-run only after required mappings are confirmed.

**Alternative / error flow:**

- If a required field has only a medium confidence match, web app requires confirmation before dry-run.
- If a required field is unmapped, web app blocks dry-run and submit.
- If booking date options changed, web app asks user to reselect booking dates.
- If the parser cannot confidently read the form structure, web app shows the raw detected fields and asks for manual review.

## Implementation Direction

- Runtime values live in `tara-caraka-form.config.json`, not in `tara-caraka-form.ps1`. The PowerShell script reads config at run time.
- Google Form metadata and confirmed field mappings are stored in `form-profile.json`, separate from default answer values.
- Field aliases and fuzzy matching handle label variations and typos. Uncertain mappings block dry-run and submit until the user reviews them.
- Real submit runs through a background PowerShell scheduler process started by FastAPI. FastAPI returns immediately; it does not hold the HTTP request open.
- Config changes to payload fields invalidate the previous dry-run via `configUpdatedAt`. The user must re-run dry-run before submit if payload fields changed.
- Sessions (`sessionId` + `sessionLabel`) group runs by booking cycle. The flow diagram and logs both filter by current session.
- Only fixed predefined actions are exposed through the web UI:
  - parse form
  - review mapping
  - update config
  - dry-run / view dry-run result
  - prepare submit
  - confirm submit
  - cancel scheduler
  - status
  - reset form / runs / lock
  - test submit (developer only)

## Safety Rules

- Cloudflare Access is required for the UI.
- Submit must require a confirmation step.
- Use a lock file to prevent duplicate active scheduler runs.
- Log all dry-run and submit attempts.
- Prevent laptop sleep during the submit scheduler window.
- Keep submit-time work minimal to reduce avoidable timing delay.
- Never expose raw command execution in the web UI.
- Keep webhook/public automation separate from the UI if needed later.

## Deferred / Not Chosen

- WhatsApp Business Cloud API: blocked by Meta business account restriction and more complex than needed.
- WhatsApp personal automation: not recommended due to reliability and policy risk.
- Discord bot: possible, but unnecessary if a web UI is enough.
- Telegram bot: possible and easy, but a custom web panel gives better control and visibility.
- n8n: useful, but not necessary as the primary interface for the final chosen flow.
