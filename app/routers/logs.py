from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from collections import defaultdict

from app.services.scheduler_runner import list_runs, get_run, read_log
from app.render import render
router    = APIRouter(prefix="/logs")


@router.get("/", response_class=HTMLResponse)
async def logs_page(request: Request):
    runs = list_runs()

    # Group runs by sessionId
    session_map: dict[str, dict] = {}
    no_session = []

    for run in runs:
        sid = run.get("sessionId", "")
        if not sid:
            no_session.append(run)
            continue
        if sid not in session_map:
            session_map[sid] = {
                "sessionId": sid,
                "sessionLabel": run.get("sessionLabel", sid),
                "runs": [],
            }
        log_lines = read_log(run["runId"]).splitlines()[-15:]
        session_map[sid]["runs"].append({**run, "logPreview": log_lines})

    # Sort sessions newest first (by first run's startedAt)
    sessions = sorted(
        session_map.values(),
        key=lambda s: s["runs"][0]["startedAt"] if s["runs"] else "",
        reverse=True,
    )

    return render(request, "logs.html", {
        "sessions": sessions,
        "no_session": no_session,
    })


@router.get("/{run_id}", response_class=HTMLResponse)
async def log_detail(request: Request, run_id: str):
    run = get_run(run_id)
    log_text = read_log(run_id) if run else "(run tidak ditemukan)"
    return render(request, "log_detail.html", {
        "run": run,
        "run_id": run_id,
        "log_text": log_text,
    })


@router.get("/{run_id}/fragment", response_class=HTMLResponse)
async def log_fragment(request: Request, run_id: str):
    """Partial: log text only, for inline HTMX polling."""
    run = get_run(run_id)
    log_text = read_log(run_id)
    done = run and run.get("status") not in ("scheduled",)

    redirect_url = None
    if done and run:
        mode = run.get("mode", "")
        if mode in ("dryrun", "dryrun-ps1"):
            redirect_url = f"/dryrun/result/{run_id}"

    return render(request, "log_fragment.html", {
        "run_id": run_id,
        "log_text": log_text,
        "done": done,
        "redirect_url": redirect_url,
    })
