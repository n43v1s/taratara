from app.services.config_handler import (
    get_config, get_form_profile, validate_config, REQUIRED_FIELDS
)

REQUIRED_MAPPINGS = [
    "childName", "birthInfo", "childAge", "gender", "religion",
    "parentName", "phoneNumber", "address", "allergy", "bookingDates",
]


def check_ready(require_dryrun: bool = True) -> dict:
    """
    Run all pre-flight checks. Returns a dict with:
      - ready: bool — True only if all checks pass
      - blocking: list[str] — human-readable blocking issues
      - warnings: list[str] — non-blocking notices
    """
    blocking = []
    warnings = []

    config = get_config()
    profile = get_form_profile()

    # 1. Config completeness
    missing_config = validate_config(config)
    if missing_config:
        blocking.append(f"Config belum lengkap — field kosong: {', '.join(missing_config)}")

    # 2. Form profile parsed
    if not profile.get("responseUrl"):
        blocking.append("Google Form belum di-parse — jalankan Form Parser terlebih dahulu.")

    # 3. Required field mappings confirmed
    mappings = profile.get("mappings", {})
    if profile.get("fields"):
        missing_mappings = [f for f in REQUIRED_MAPPINGS if f not in mappings]
        if missing_mappings:
            blocking.append(
                f"Mapping belum dikonfirmasi untuk: {', '.join(missing_mappings)}"
            )
    elif profile.get("responseUrl"):
        blocking.append("Field mapping belum ada — jalankan Review Mapping terlebih dahulu.")

    # 4. Booking dates selected and valid
    booking_dates = config.get("bookingDates", [])
    if not booking_dates:
        blocking.append("Tanggal booking belum dipilih.")
    else:
        # Check dates exist in form options
        available = _get_available_dates(profile, mappings)
        if available:
            invalid = [d for d in booking_dates if d not in available]
            if invalid:
                blocking.append(
                    f"Tanggal booking tidak tersedia di form: {', '.join(invalid)} — "
                    "parse ulang form dan pilih ulang tanggal."
                )

    # 5. Dryrun harus dijalankan setelah config terakhir disimpan (hanya untuk submit)
    if not require_dryrun:
        return {"ready": len(blocking) == 0, "blocking": blocking, "warnings": warnings}
    from app.services.scheduler_runner import list_runs
    config_updated_at = config.get("configUpdatedAt", "")
    session_id = profile.get("sessionId", "")
    runs = list_runs()
    session_runs = [r for r in runs if r.get("sessionId") == session_id] if session_id else runs
    dryrun_valid = any(
        r.get("mode") in ("dryrun", "dryrun-ps1")
        and r.get("status") == "success"
        and r.get("startedAt", "") >= config_updated_at
        for r in session_runs
    )
    if not dryrun_valid:
        blocking.append("Dry run belum dijalankan setelah config terakhir disimpan.")

    # 6. Warnings (non-blocking)
    if profile.get("responseUrl") and not mappings:
        warnings.append("Form sudah di-parse tapi mapping belum dikonfirmasi.")

    return {
        "ready": len(blocking) == 0,
        "blocking": blocking,
        "warnings": warnings,
    }


def check_no_active_scheduler(allow_test: bool = False) -> str | None:
    """
    Return error message if a real submit scheduler lock exists, else None.
    If allow_test=True, ignore locks that belong to submit-test runs.
    """
    from pathlib import Path
    from app.services.scheduler_runner import list_runs
    lock_file = Path(__file__).parent.parent.parent / "data" / "scheduler.lock"
    if not lock_file.exists():
        return None
    try:
        run_id = lock_file.read_text(encoding="utf-8").strip()
        if allow_test:
            runs = list_runs()
            locked_run = next((r for r in runs if r.get("runId") == run_id), None)
            if locked_run and locked_run.get("mode") == "submit-test":
                return None
        return f"Scheduler sedang aktif (lock: {run_id}). Batalkan dulu sebelum memulai yang baru."
    except Exception:
        return "Scheduler lock file ada tapi tidak bisa dibaca."


def _get_available_dates(profile: dict, mappings: dict) -> list[str]:
    booking_entry_id = mappings.get("bookingDates", "")
    for field in profile.get("fields", []):
        if field.get("entryId") == booking_entry_id and field.get("options"):
            return field["options"]
    return []
