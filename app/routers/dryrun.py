import json
import subprocess
import sys
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.services.validator import check_ready
from app.services.scheduler_runner import get_run, read_log, _new_run_id, RUNS_DIR, LOGS_DIR
from app.services.config_handler import get_form_profile
from app.render import render

router = APIRouter(prefix="/dryrun")


@router.get("/", response_class=HTMLResponse)
async def dryrun_page(request: Request):
    check = check_ready(require_dryrun=False)
    return render(request, "dryrun.html", {
        "check": check,
        "result": None,
    })


@router.post("/run", response_class=HTMLResponse)
async def dryrun_run(request: Request):
    check = check_ready(require_dryrun=False)
    if not check["ready"]:
        return render(request, "dryrun.html", {
            "check": check,
            "result": None,
        })

    run_id = _new_run_id()
    profile = get_form_profile()

    # Save pending run record so the log fragment can poll it
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    run_record = {
        "runId": run_id,
        "sessionId": profile.get("sessionId", ""),
        "sessionLabel": profile.get("sessionLabel", ""),
        "mode": "dryrun-ps1",
        "startedAt": datetime.now().isoformat(),
        "status": "scheduled",
        "logFile": str(LOGS_DIR / f"{run_id}.log"),
    }
    (RUNS_DIR / f"{run_id}.json").write_text(
        json.dumps(run_record, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    try:
        cmd = [
            sys.executable,
            "-m", "app.scheduler_cli",
            "--mode", "dryrun",
            "--run-id", run_id,
            "--record-mode", "dryrun",
        ]
        subprocess.Popen(
            cmd,
            close_fds=True,
        )
    except Exception as e:
        run_record["status"] = "error"
        (RUNS_DIR / f"{run_id}.json").write_text(
            json.dumps(run_record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return render(request, "dryrun.html", {
            "check": check,
            "result": {"runId": run_id, "status": "error", "logLines": [str(e)]},
        })

    # Show live log polling view
    return render(request, "dryrun.html", {
        "check": check,
        "result": {"runId": run_id, "status": "scheduled", "logLines": []},
    })


@router.get("/result/{run_id}", response_class=HTMLResponse)
async def dryrun_result(request: Request, run_id: str):
    from app.services.scheduler_runner import build_payload
    from app.services.config_handler import get_config

    check = check_ready(require_dryrun=False)
    run = get_run(run_id)
    if not run:
        return render(request, "dryrun.html", {
            "check": check, "result": None,
        })

    log_lines = read_log(run_id).splitlines()
    profile = get_form_profile()
    config  = get_config()

    # PS-mode dryruns don't store payload in run record — rebuild it
    payload = run.get("payload") or build_payload(config, profile)
    mappings = profile.get("mappings", {})
    entry_to_field = {v: k for k, v in mappings.items()}

    result = {**run, "logLines": log_lines, "payload": payload, "entryToField": entry_to_field}
    return render(request, "dryrun.html", {
        "check": check,
        "result": result,
    })
