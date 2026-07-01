"""Tests for config_handler service."""
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch


VALID_CONFIG = {
    "childName":   "Tara",
    "birthInfo":   "Jakarta, 01 Jan 2022",
    "childAge":    "3 s/d 15",
    "gender":      "Perempuan",
    "religion":    "Kristen",
    "parentName":  "Agus",
    "satker":      "Setjen",
    "phoneNumber": "081234",
    "address":     "Jl. A",
    "allergy":     "Tidak ada",
    "bookingDates": ["01 Juli"],
}

EMPTY_CONFIG = {k: ("" if k != "bookingDates" else []) for k in VALID_CONFIG}


def test_validate_config_valid():
    from app.services.config_handler import validate_config
    missing = validate_config(VALID_CONFIG)
    assert missing == []


def test_validate_config_all_empty():
    from app.services.config_handler import validate_config
    missing = validate_config(EMPTY_CONFIG)
    assert len(missing) == len(VALID_CONFIG)


def test_validate_config_missing_booking_dates():
    from app.services.config_handler import validate_config
    config = {**VALID_CONFIG, "bookingDates": []}
    missing = validate_config(config)
    assert "bookingDates" in missing


def test_validate_config_missing_one_field():
    from app.services.config_handler import validate_config
    config = {**VALID_CONFIG, "childName": ""}
    missing = validate_config(config)
    assert "childName" in missing
    assert len(missing) == 1


def test_save_and_read_config():
    from app.services.config_handler import save_config, get_config
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / "config.json"
        with patch("app.services.config_handler.CONFIG_FILE", tmp_file):
            save_config(VALID_CONFIG)
            loaded = get_config()
    assert loaded["childName"] == "Tara"
    assert loaded["bookingDates"] == ["01 Juli"]


def test_save_and_read_form_profile():
    from app.services.config_handler import save_form_profile, get_form_profile
    profile = {"formId": "abc", "responseUrl": "https://example.com", "fields": [], "mappings": {}}
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / "profile.json"
        with patch("app.services.config_handler.FORM_PROFILE_FILE", tmp_file):
            save_form_profile(profile)
            loaded = get_form_profile()
    assert loaded["formId"] == "abc"
