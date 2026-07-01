from app.services.config_handler import get_config, get_form_profile, validate_config
from app.services.scheduler_runner import list_runs
from pathlib import Path

DATA_DIR  = Path(__file__).parent.parent.parent / "data"
LOCK_FILE = DATA_DIR / "scheduler.lock"

REQUIRED_MAPPINGS = [
    "childName", "birthInfo", "childAge", "gender", "religion",
    "parentName", "phoneNumber", "address", "allergy", "bookingDates",
]


def get_flow_state() -> dict:
    """
    Return state of each step in the workflow.
    State: "done" | "ready" | "blocked"
    """
    config  = get_config()
    profile = get_form_profile()

    # Step 1: Form Parser
    form_done = bool(profile.get("responseUrl"))

    # Step 2: Mapping
    mappings = profile.get("mappings", {})
    mapping_done = form_done and all(f in mappings for f in REQUIRED_MAPPINGS)

    # Step 3: Config
    config_done = mapping_done and validate_config(config) == []

    # Step 4: Dry Run — at least one successful dryrun in current session
    runs = list_runs()
    current_session = profile.get("sessionId", "")
    session_runs = [r for r in runs if r.get("sessionId") == current_session] if current_session else []

    config_updated_at = config.get("configUpdatedAt", "")
    latest_dryrun = next(
        (r for r in session_runs
         if r.get("mode") in ("dryrun", "dryrun-ps1")
         and r.get("status") == "success"
         and r.get("startedAt", "") >= config_updated_at),
        None
    )
    dryrun_done = config_done and latest_dryrun is not None

    # Step 5: Submit scheduler — only real submit (not test), current session only
    latest_submit = next(
        (r for r in session_runs if r.get("mode") == "submit"), None
    )
    submit_done = bool(latest_submit and latest_submit.get("status") == "success")

    # Scheduler active only if the active lock belongs to a real submit run
    scheduler_active = False
    if LOCK_FILE.exists():
        try:
            locked_run_id = LOCK_FILE.read_text(encoding="utf-8").strip()
            locked_run = next((r for r in session_runs if r.get("runId") == locked_run_id), None)
            if locked_run and locked_run.get("mode") == "submit":
                scheduler_active = True
        except Exception:
            pass

    def state(done: bool, prev_done: bool) -> str:
        if done:
            return "done"
        if prev_done:
            return "ready"
        return "blocked"

    return {
        "steps": [
            {
                "id": "form",
                "label_key": "flow.form_parser",
                "url": "/form",
                "state": state(form_done, True),
                "detail_key": None if form_done else "flow.no_form",
                "detail_params": {},
                "detail": profile.get("responseUrl", "")[:60] if form_done else None,
            },
            {
                "id": "mapping",
                "label_key": "flow.field_mapping",
                "url": "/mapping",
                "state": state(mapping_done, form_done),
                "detail_key": "flow.mapping_confirmed" if mapping_done else "flow.mapping_pending",
                "detail_params": {"n": len(mappings)} if mapping_done else {},
                "detail": None,
            },
            {
                "id": "config",
                "label_key": "flow.config",
                "url": "/config",
                "state": state(config_done, mapping_done),
                "detail_key": "flow.config_done" if config_done else "flow.config_pending",
                "detail_params": {"name": config.get("childName", "—")} if config_done else {},
                "detail": None,
            },
            {
                "id": "dryrun",
                "label_key": "flow.dry_run",
                "url": f"/dryrun/result/{latest_dryrun['runId']}" if dryrun_done else "/dryrun",
                "state": state(dryrun_done, config_done),
                "detail_key": "flow.dryrun_done" if dryrun_done else "flow.dryrun_pending",
                "detail_params": {},
                "detail": None,
            },
            {
                "id": "submit",
                "label_key": "flow.submit_scheduler",
                "url": "/status" if (submit_done or scheduler_active) else "/submit/prepare",
                "state": "active" if scheduler_active else ("done" if submit_done else state(False, dryrun_done)),
                "detail_key": (
                    "flow.submit_active" if scheduler_active
                    else ("flow.submit_done" if submit_done else "flow.submit_pending")
                ),
                "detail_params": {"run_id": latest_submit.get("runId", "")} if scheduler_active else {},
                "detail": None,
            },
        ],
        "scheduler_active": scheduler_active,
    }
