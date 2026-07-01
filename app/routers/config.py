from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.services.config_handler import get_config, save_config, get_form_profile, validate_config
from app.render import render

router = APIRouter(prefix="/config")


@router.get("/", response_class=HTMLResponse)
async def config_page(request: Request):
    config = get_config()
    profile = get_form_profile()
    booking_options = _get_booking_options(profile)
    field_options = _get_field_options(profile)
    missing = validate_config(config)

    return render(request, "config.html", {
        "config": config,
        "booking_options": booking_options,
        "field_options": field_options,
        "missing": missing,
        "saved": False,
        "error": None,
    })


@router.post("/save", response_class=HTMLResponse)
async def save_config_route(request: Request):
    form_data = await request.form()
    profile = get_form_profile()
    booking_options = _get_booking_options(profile)

    # Build new config from form submission
    new_config = {
        "childName": form_data.get("childName", "").strip(),
        "birthInfo": form_data.get("birthInfo", "").strip(),
        "childAge": form_data.getlist("childAge") or form_data.get("childAge", "").strip(),
        "gender": form_data.get("gender", "").strip(),
        "religion": form_data.get("religion", "").strip(),
        "parentName": form_data.get("parentName", "").strip(),
        "satker": form_data.get("satker", "").strip(),
        "phoneNumber": form_data.get("phoneNumber", "").strip(),
        "address": form_data.get("address", "").strip(),
        "allergy": form_data.get("allergy", "").strip(),
        "bookingDates": form_data.getlist("bookingDates"),
        "attemptTimes": _parse_attempt_times(form_data.get("attemptTimes", "")),
    }

    # Validate booking dates against form options
    if booking_options and new_config["bookingDates"]:
        new_config["bookingDates"] = [
            d for d in new_config["bookingDates"] if d in booking_options
        ]

    # Detect if field values changed (excludes attemptTimes)
    PAYLOAD_FIELDS = ["childName", "birthInfo", "childAge", "gender", "religion",
                      "parentName", "satker", "phoneNumber", "address", "allergy", "bookingDates"]
    old_config = get_config()
    field_values_changed = any(old_config.get(f) != new_config.get(f) for f in PAYLOAD_FIELDS)

    missing = validate_config(new_config)
    save_config(new_config, field_values_changed=field_values_changed)
    field_options = _get_field_options(profile)

    return render(request, "config.html", {
        "config": new_config,
        "booking_options": booking_options,
        "field_options": field_options,
        "missing": missing,
        "saved": True,
        "error": None,
    })


def _parse_attempt_times(raw: str) -> list[str]:
    """Parse newline or comma-separated HH:MM:SS times."""
    import re
    times = re.split(r"[\n,]+", raw)
    result = []
    for t in times:
        t = t.strip()
        if re.match(r"^\d{2}:\d{2}:\d{2}$", t):
            result.append(t)
    return result or ["12:59:58", "12:59:59", "13:00:00"]


def _get_field_options(profile: dict) -> dict:
    """Return {internal_field: [options]} for all mapped fields that have options."""
    mappings = profile.get("mappings", {})
    fields_by_entry = {f["entryId"]: f for f in profile.get("fields", [])}
    result = {}
    for internal, entry_id in mappings.items():
        field = fields_by_entry.get(entry_id, {})
        opts = field.get("options", [])
        if opts:
            result[internal] = opts
    return result


def _get_booking_options(profile: dict) -> list[str]:
    """Extract booking date options from the parsed form profile."""
    for field in profile.get("fields", []):
        if field.get("options") and "Juni" in " ".join(field["options"] or []) or \
           "Juli" in " ".join(field["options"] or []) or \
           field.get("type") == "checkbox" and field.get("options"):
            mappings = profile.get("mappings", {})
            if mappings.get("bookingDates") == field["entryId"]:
                return field["options"]
    # Fallback: find checkbox field with most options
    for field in profile.get("fields", []):
        if field.get("type") == "checkbox" and field.get("options"):
            return field["options"]
    return []
