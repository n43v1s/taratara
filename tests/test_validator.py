"""Tests for validator service."""
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

VALID_PROFILE = {
    "formUrl":     "https://forms.gle/xxx",
    "formId":      "abc",
    "responseUrl": "https://docs.google.com/forms/d/e/abc/formResponse",
    "fbzx":        "-123",
    "fields": [
        {"label": "Nama Anak",       "entryId": "entry.111", "type": "short_text", "options": []},
        {"label": "Tanggal Booking", "entryId": "entry.333", "type": "checkbox",   "options": ["01 Juli", "02 Juli"]},
    ],
    "mappings": {
        "childName":    "entry.111",
        "birthInfo":    "entry.112",
        "childAge":     "entry.113",
        "gender":       "entry.114",
        "religion":     "entry.115",
        "parentName":   "entry.116",
        "phoneNumber":  "entry.117",
        "address":      "entry.118",
        "allergy":      "entry.119",
        "bookingDates": "entry.333",
    },
}


def _make_check(config=None, profile=None):
    with patch("app.services.validator.get_config", return_value=config or VALID_CONFIG), \
         patch("app.services.validator.get_form_profile", return_value=profile or VALID_PROFILE):
        from app.services.validator import check_ready
        return check_ready()


def test_check_ready_all_valid():
    result = _make_check()
    assert result["ready"] is True
    assert result["blocking"] == []


def test_check_ready_empty_config():
    empty = {k: ("" if k != "bookingDates" else []) for k in VALID_CONFIG}
    result = _make_check(config=empty)
    assert result["ready"] is False
    assert any("Config" in b for b in result["blocking"])


def test_check_ready_no_response_url():
    profile = {**VALID_PROFILE, "responseUrl": ""}
    result = _make_check(profile=profile)
    assert result["ready"] is False
    assert any("parse" in b.lower() for b in result["blocking"])


def test_check_ready_missing_mappings():
    profile = {**VALID_PROFILE, "mappings": {}}
    result = _make_check(profile=profile)
    assert result["ready"] is False
    assert any("mapping" in b.lower() for b in result["blocking"])


def test_check_ready_no_booking_dates():
    config = {**VALID_CONFIG, "bookingDates": []}
    result = _make_check(config=config)
    assert result["ready"] is False
    assert any("booking" in b.lower() for b in result["blocking"])


def test_check_ready_invalid_booking_date():
    config = {**VALID_CONFIG, "bookingDates": ["99 Desember"]}
    result = _make_check(config=config)
    assert result["ready"] is False
    assert any("tidak tersedia" in b for b in result["blocking"])


def test_check_no_active_scheduler_no_lock():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_lock = Path(tmpdir) / "scheduler.lock"
        # fake_lock does not exist — patch the lock file path directly
        with patch("app.services.validator.check_no_active_scheduler",
                   wraps=lambda: None if not fake_lock.exists() else "active"):
            from app.services.validator import check_no_active_scheduler
            result = check_no_active_scheduler()
            assert result is None
