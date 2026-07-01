import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent.parent / "data"

CONFIG_FILE = DATA_DIR / "tara-caraka-form.config.json"
FORM_PROFILE_FILE = DATA_DIR / "form-profile.json"
FIELD_ALIASES_FILE = DATA_DIR / "field-aliases.json"

REQUIRED_FIELDS = [
    "childName", "birthInfo", "childAge", "gender", "religion",
    "parentName", "satker", "phoneNumber", "address", "allergy",
]


def _read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_config() -> dict:
    return _read_json(CONFIG_FILE)


def save_config(data: dict, field_values_changed: bool = True) -> None:
    from datetime import datetime
    if field_values_changed:
        data["configUpdatedAt"] = datetime.now().isoformat()
    _write_json(CONFIG_FILE, data)


def get_form_profile() -> dict:
    return _read_json(FORM_PROFILE_FILE)


def save_form_profile(data: dict) -> None:
    _write_json(FORM_PROFILE_FILE, data)


def get_field_aliases() -> dict:
    return _read_json(FIELD_ALIASES_FILE)


def validate_config(config: dict) -> list[str]:
    """Return list of missing required field names."""
    missing = []
    for field in REQUIRED_FIELDS:
        value = config.get(field, "")
        if not value or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    if not config.get("bookingDates"):
        missing.append("bookingDates")
    return missing
