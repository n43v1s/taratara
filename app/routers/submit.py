import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.validator import check_ready, check_no_active_scheduler
from app.services.config_handler import get_config, get_form_profile
from app.services.scheduler_runner import build_payload, _new_run_id, RUNS_DIR, LOGS_DIR
from app.render import render

BASE_DIR = Path(__file__).parent.parent
DATA_DIR  = BASE_DIR.parent / "data"
LOCK_FILE = DATA_DIR / "scheduler.lock"
router = APIRouter(prefix="/submit")


# ---------------------------------------------------------------------------
# Prepare Submit
# ---------------------------------------------------------------------------
@router.get("/prepare", response_class=HTMLResponse)
async def prepare_page(request: Request):
    check = check_ready()
    lock_error = check_no_active_scheduler()
    config = get_config()
    profile = get_form_profile()
    payload = build_payload(config, profile) if check["ready"] else {}
    mappings = profile.get("mappings", {})
    entry_to_field = {v: k for k, v in mappings.items()}

    attempt_times = config.get("attemptTimes") or ["12:59:58", "12:59:59", "13:00:00"]

    return render(request, "submit_prepare.html", {
        "check": check,
        "lock_error": lock_error,
        "config": config,
        "profile": profile,
        "payload": payload,
        "entry_to_field": entry_to_field,
        "attempt_times": attempt_times,
    })


# ---------------------------------------------------------------------------
# Confirm Submit
# ---------------------------------------------------------------------------
@router.post("/confirm", response_class=HTMLResponse)
async def confirm_submit(request: Request):
    check = check_ready()
    if not check["ready"]:
        return RedirectResponse("/submit/prepare", status_code=303)

    lock_error = check_no_active_scheduler()
    if lock_error:
        return render(request, "submit_result.html", {
            "success": False,
            "message": lock_error,
            "run_id": None,
        })

    run_id = _new_run_id()

    # Launch Ubuntu-native Python scheduler as a background process.
    try:
        cmd = [
            sys.executable,
            "-m", "app.scheduler_cli",
            "--mode", "submit",
            "--run-id", run_id,
            "--record-mode", "submit",
        ]
        subprocess.Popen(
            cmd,
            close_fds=True,
        )
    except Exception as e:
        return render(request, "submit_result.html", {
            "success": False,
            "message": f"Gagal menjalankan scheduler: {e}",
            "run_id": None,
        })

    # Save pending run record
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    profile = get_form_profile()
    run_record = {
        "runId": run_id,
        "sessionId": profile.get("sessionId", ""),
        "sessionLabel": profile.get("sessionLabel", ""),
        "mode": "submit",
        "startedAt": datetime.now().isoformat(),
        "status": "scheduled",
        "logFile": str(LOGS_DIR / f"{run_id}.log"),
    }
    (RUNS_DIR / f"{run_id}.json").write_text(
        json.dumps(run_record, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return render(request, "submit_result.html", {
        "success": True,
        "message": "Scheduler berhasil dijalankan. Form akan dikirim sesuai jadwal.",
        "run_id": run_id,
    })


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Test Submit (developer only)
# ---------------------------------------------------------------------------
@router.post("/test", response_class=HTMLResponse)
async def test_submit(request: Request, delay_seconds: int = Form(30)):
    delay_seconds = max(5, min(delay_seconds, 3600))
    check = check_ready()
    if not check["ready"]:
        return render(request, "test_submit_result.html", {
            "success": False,
            "message": "Belum siap: " + "; ".join(check.get("blocking", [])),
            "run_id": None,
        })

    lock_error = check_no_active_scheduler(allow_test=True)
    if lock_error:
        return render(request, "test_submit_result.html", {
            "success": False,
            "message": lock_error,
            "run_id": None,
        })

    run_id = _new_run_id()

    # Schedule 3 attempts starting at delay_seconds from now
    now = datetime.now()
    attempt_times = ",".join(
        (now + timedelta(seconds=delay_seconds + i)).strftime("%H:%M:%S") for i in range(3)
    )

    try:
        cmd = [
            sys.executable,
            "-m", "app.scheduler_cli",
            "--mode", "submit",
            "--run-id", run_id,
            "--record-mode", "submit-test",
            "--attempt-times-override", attempt_times,
        ]
        subprocess.Popen(
            cmd,
            close_fds=True,
        )
    except Exception as e:
        return render(request, "test_submit_result.html", {
            "success": False,
            "message": f"Gagal menjalankan test scheduler: {e}",
            "run_id": None,
        })

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    profile = get_form_profile()
    run_record = {
        "runId": run_id,
        "sessionId": profile.get("sessionId", ""),
        "sessionLabel": profile.get("sessionLabel", ""),
        "mode": "submit-test",
        "startedAt": datetime.now().isoformat(),
        "status": "scheduled",
        "attemptTimesOverride": attempt_times,
        "logFile": str(LOGS_DIR / f"{run_id}.log"),
    }
    (RUNS_DIR / f"{run_id}.json").write_text(
        json.dumps(run_record, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return render(request, "test_submit_result.html", {
        "success": True,
        "message": f"Attempt dijadwalkan pukul {attempt_times.replace(',', ', ')}.",
        "run_id": run_id,
    })


@router.post("/cancel", response_class=HTMLResponse)
async def cancel_submit(request: Request):
    if not LOCK_FILE.exists():
        return render(request, "submit_result.html", {
            "success": False,
            "message": "Tidak ada scheduler yang aktif.",
            "run_id": None,
        })

    run_id = LOCK_FILE.read_text(encoding="utf-8").strip()
    LOCK_FILE.unlink(missing_ok=True)

    # Update run record status
    run_file = RUNS_DIR / f"{run_id}.json"
    if run_file.exists():
        try:
            record = json.loads(run_file.read_text(encoding="utf-8"))
            record["status"] = "cancelled"
            record["cancelledAt"] = datetime.now().isoformat()
            run_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    return render(request, "submit_result.html", {
        "success": True,
        "message": f"Scheduler dibatalkan. Lock dihapus. Run ID: {run_id}",
        "run_id": run_id,
    })
