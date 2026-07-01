import json
from pathlib import Path

from fastapi import APIRouter, Request, Header
from fastapi.responses import HTMLResponse, RedirectResponse

from app.render import render

DATA_DIR  = Path(__file__).parent.parent.parent / "data"
router    = APIRouter(prefix="/reset")

PROFILE_FILE = DATA_DIR / "form-profile.json"
LOCK_FILE    = DATA_DIR / "scheduler.lock"
RUNS_DIR     = DATA_DIR / "runs"
LOGS_DIR     = DATA_DIR / "logs"


@router.get("/", response_class=HTMLResponse)
async def reset_page(request: Request):
    profile = _load_profile()
    has_profile = bool(profile.get("formId"))
    has_mappings = bool(profile.get("mappings"))
    has_runs = any(RUNS_DIR.glob("*.json")) if RUNS_DIR.exists() else False
    has_lock = LOCK_FILE.exists()
    return render(request, "reset.html", {
        "has_profile": has_profile,
        "has_mappings": has_mappings,
        "has_runs": has_runs,
        "has_lock": has_lock,
        "session_label": profile.get("sessionLabel", ""),
        "session_id": profile.get("sessionId", ""),
    })


@router.post("/form", response_class=HTMLResponse)
async def reset_form(request: Request, hx_request: str | None = Header(default=None)):
    """Clear form-profile.json (resets parsed form + mappings)."""
    PROFILE_FILE.write_text("{}", encoding="utf-8")
    if hx_request:
        return render(request, "reset_result.html", {
            "action": "Form & Mapping",
            "message": "Form profile dan semua mapping berhasil dihapus. Silakan parse form baru.",
        })
    return RedirectResponse("/form", status_code=303)


@router.post("/runs", response_class=HTMLResponse)
async def reset_runs(request: Request):
    """Delete all run records and logs."""
    deleted_runs = 0
    deleted_logs = 0
    if RUNS_DIR.exists():
        for f in RUNS_DIR.glob("*.json"):
            f.unlink(missing_ok=True)
            deleted_runs += 1
    if LOGS_DIR.exists():
        for f in LOGS_DIR.glob("*.log"):
            f.unlink(missing_ok=True)
            deleted_logs += 1
    return render(request, "reset_result.html", {
        "action": "Riwayat Run",
        "message": f"Dihapus: {deleted_runs} run record, {deleted_logs} log file.",
    })


@router.post("/lock", response_class=HTMLResponse)
async def reset_lock(request: Request):
    """Remove scheduler lock file."""
    if LOCK_FILE.exists():
        run_id = LOCK_FILE.read_text(encoding="utf-8").strip()
        LOCK_FILE.unlink(missing_ok=True)
        msg = f"Lock dihapus (Run ID: {run_id})."
    else:
        msg = "Tidak ada lock aktif."
    return render(request, "reset_result.html", {
        "action": "Scheduler Lock",
        "message": msg,
    })


def _load_profile() -> dict:
    if not PROFILE_FILE.exists():
        return {}
    try:
        return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
