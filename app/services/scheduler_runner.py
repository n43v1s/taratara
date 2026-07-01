import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.services.config_handler import get_config, get_form_profile

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RUNS_DIR = DATA_DIR / "runs"
LOGS_DIR = DATA_DIR / "logs"


def build_payload(config: dict, profile: dict) -> dict:
    """Build the Google Form POST payload from config and confirmed mappings."""
    mappings = profile.get("mappings", {})
    payload = {}

    for internal_field, entry_id in mappings.items():
        value = config.get(internal_field)
        if value is None:
            continue
        if isinstance(value, list):
            # Checkbox fields: multiple values under same key
            payload[entry_id] = value
        else:
            payload[entry_id] = str(value)

    # Always include fbzx if available
    if profile.get("fbzx"):
        payload["fbzx"] = profile["fbzx"]

    return payload


def run_dryrun() -> dict:
    """
    Execute a dry-run: build payload, log it, save run record.
    Returns run record dict.
    """
    run_id = _new_run_id()
    started_at = datetime.now().isoformat()

    config = get_config()
    profile = get_form_profile()

    payload = build_payload(config, profile)

    log_lines = [
        f"[DRY-RUN] Run ID   : {run_id}",
        f"[DRY-RUN] Started  : {started_at}",
        f"[DRY-RUN] Endpoint : {profile.get('responseUrl', '(unknown)')}",
        f"[DRY-RUN] fbzx     : {profile.get('fbzx', '(none)')}",
        "",
        "[DRY-RUN] Payload preview:",
    ]

    for key, value in payload.items():
        if isinstance(value, list):
            for v in value:
                log_lines.append(f"  {key} = {v}")
        else:
            log_lines.append(f"  {key} = {value}")

    log_lines += [
        "",
        "[DRY-RUN] Form tidak dikirim. Ini adalah simulasi saja.",
        "[DRY-RUN] Status: SUCCESS",
    ]

    log_text = "\n".join(log_lines)

    # Write log file
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{run_id}.log"
    log_file.write_text(log_text, encoding="utf-8")

    # Build run record
    run_record = {
        "runId": run_id,
        "sessionId": profile.get("sessionId", ""),
        "sessionLabel": profile.get("sessionLabel", ""),
        "mode": "dryrun",
        "startedAt": started_at,
        "status": "success",
        "responseUrl": profile.get("responseUrl", ""),
        "payload": payload,
        "logFile": str(log_file),
        "configSnapshot": {k: v for k, v in config.items()},
    }

    # Save run record
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_file = RUNS_DIR / f"{run_id}.json"
    run_file.write_text(json.dumps(run_record, ensure_ascii=False, indent=2), encoding="utf-8")

    # Build entry_id -> internal field name lookup for display
    mappings = profile.get("mappings", {})
    entry_to_field = {v: k for k, v in mappings.items()}
    run_record["entryToField"] = entry_to_field

    run_record["logLines"] = log_lines
    return run_record


def _new_run_id() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    short = str(uuid.uuid4())[:6]
    return f"run-{ts}-{short}"


def list_runs() -> list[dict]:
    """Return list of run records sorted newest first."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    runs = []
    for f in sorted(RUNS_DIR.glob("*.json"), reverse=True):
        try:
            runs.append(json.loads(f.read_text(encoding="utf-8-sig")))
        except Exception:
            continue
    return runs


def get_run(run_id: str) -> dict | None:
    run_file = RUNS_DIR / f"{run_id}.json"
    if not run_file.exists():
        return None
    try:
        return json.loads(run_file.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def read_log(run_id: str) -> str:
    log_file = LOGS_DIR / f"{run_id}.log"
    if not log_file.exists():
        return "(log tidak ditemukan)"
    return log_file.read_text(encoding="utf-8-sig")
