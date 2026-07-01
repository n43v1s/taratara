from fastapi import APIRouter, Request, Form as FormData
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Annotated

from app.services.config_handler import get_form_profile, save_form_profile
from app.services.field_matcher import match_fields, INTERNAL_FIELDS
from app.render import render

router = APIRouter(prefix="/mapping")

INTERNAL_FIELD_LABELS = {
    "childName": "Nama Anak",
    "birthInfo": "Tempat Tanggal Lahir",
    "childAge": "Usia Anak",
    "gender": "Jenis Kelamin",
    "religion": "Agama",
    "parentName": "Nama Orang Tua",
    "satker": "Satker",
    "phoneNumber": "No HP",
    "address": "Alamat",
    "allergy": "Alergi",
    "bookingDates": "Tanggal Booking",
}


@router.get("/", response_class=HTMLResponse)
async def mapping_page(request: Request):
    profile = get_form_profile()

    if not profile.get("fields"):
        return render(request, "mapping.html", {
            "matches": [],
            "internal_fields": INTERNAL_FIELDS,
            "internal_field_labels": INTERNAL_FIELD_LABELS,
            "saved": False,
            "error": "Belum ada form yang di-parse. Silakan parse Google Form terlebih dahulu.",
        })

    # If mappings already confirmed, load them; otherwise run matcher
    if profile.get("mappings"):
        matches = _load_confirmed_matches(profile)
    else:
        matches = match_fields(profile["fields"])

    return render(request, "mapping.html", {
        "matches": matches,
        "internal_fields": INTERNAL_FIELDS,
        "internal_field_labels": INTERNAL_FIELD_LABELS,
        "saved": False,
        "error": None,
    })


@router.post("/confirm", response_class=HTMLResponse)
async def confirm_mapping(request: Request):
    form_data = await request.form()
    profile = get_form_profile()

    if not profile.get("fields"):
        return RedirectResponse("/mapping", status_code=303)

    # Rebuild matches from submitted form data
    matches = match_fields(profile["fields"])
    mappings = {}

    for i, match in enumerate(matches):
        entry_id = match["entryId"]
        chosen = form_data.get(f"mapping_{i}", "").strip()
        if chosen:
            mappings[chosen] = entry_id

    profile["mappings"] = mappings
    save_form_profile(profile)

    # Reload with confirmed status
    confirmed_matches = _load_confirmed_matches(profile)
    return render(request, "mapping.html", {
        "matches": confirmed_matches,
        "internal_fields": INTERNAL_FIELDS,
        "internal_field_labels": INTERNAL_FIELD_LABELS,
        "saved": True,
        "error": None,
    })


def _load_confirmed_matches(profile: dict) -> list[dict]:
    """Reconstruct match list from saved mappings for display."""
    mappings = profile.get("mappings", {})
    # Invert: entry_id -> internal_field
    entry_to_internal = {v: k for k, v in mappings.items()}

    matches = []
    for field in profile["fields"]:
        entry_id = field["entryId"]
        internal = entry_to_internal.get(entry_id, "")
        matches.append({
            "label": field["label"],
            "entryId": entry_id,
            "type": field["type"],
            "options": field["options"],
            "internalField": internal,
            "confidence": 100 if internal else 0,
            "status": "confirmed" if internal else "unmapped",
        })
    return matches
