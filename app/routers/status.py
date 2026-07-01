from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pathlib import Path
import json

from app.services.scheduler_runner import list_runs, read_log
from app.render import render

BASE_DIR  = Path(__file__).parent.parent
DATA_DIR  = BASE_DIR.parent / "data"
LOCK_FILE = DATA_DIR / "scheduler.lock"
router = APIRouter(prefix="/status")

LOG_TAIL_LINES = 30


@router.get("/", response_class=HTMLResponse)
async def status_page(request: Request):
    # Scheduler active?
    active = LOCK_FILE.exists()
    active_run_id = None
    if active:
        try:
            active_run_id = LOCK_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    # Latest run
    runs = list_runs()
    latest = runs[0] if runs else None

    # Log tail
    log_tail = []
    target_run_id = active_run_id or (latest["runId"] if latest else None)
    if target_run_id:
        log_text = read_log(target_run_id)
        log_tail = log_text.splitlines()[-LOG_TAIL_LINES:]

    return render(request, "status.html", {
        "active": active,
        "active_run_id": active_run_id,
        "latest": latest,
        "log_tail": log_tail,
        "target_run_id": target_run_id,
    })
