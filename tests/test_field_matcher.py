"""Tests for field_matcher service."""
import pytest
from unittest.mock import patch

MOCK_ALIASES = {
    "childName":   ["Nama Anak", "Nama Lengkap Anak"],
    "parentName":  ["Nama Orang Tua", "Nama Orangtua", "Nama Ortu", "NAMA ORAGTUA"],
    "bookingDates":["Tanggal Booking", "Pilih Tanggal"],
    "gender":      ["Jenis Kelamin"],
    "phoneNumber": ["No Hp", "Nomor HP"],
}

MOCK_FIELDS = [
    {"label": "Nama Anak",       "entryId": "entry.111", "type": "short_text", "options": []},
    {"label": "Nama Ortu",       "entryId": "entry.222", "type": "short_text", "options": []},
    {"label": "Tanggal Booking", "entryId": "entry.333", "type": "checkbox",   "options": ["01 Juli"]},
    {"label": "NAMA ORAGTUA",    "entryId": "entry.444", "type": "short_text", "options": []},
    {"label": "No Hp",           "entryId": "entry.555", "type": "short_text", "options": []},
    {"label": "ZZZUnknownField", "entryId": "entry.666", "type": "short_text", "options": []},
]


@patch("app.services.field_matcher.get_field_aliases", return_value=MOCK_ALIASES)
def test_exact_alias_match(mock_aliases):
    from app.services.field_matcher import match_fields
    results = match_fields(MOCK_FIELDS[:1])
    assert results[0]["internalField"] == "childName"
    assert results[0]["confidence"] == 100
    assert results[0]["status"] == "auto"


@patch("app.services.field_matcher.get_field_aliases", return_value=MOCK_ALIASES)
def test_alias_match_nama_ortu(mock_aliases):
    from app.services.field_matcher import match_fields
    results = match_fields([MOCK_FIELDS[1]])
    assert results[0]["internalField"] == "parentName"
    assert results[0]["status"] == "auto"


@patch("app.services.field_matcher.get_field_aliases", return_value=MOCK_ALIASES)
def test_alias_match_typo_oragtua(mock_aliases):
    from app.services.field_matcher import match_fields
    results = match_fields([MOCK_FIELDS[3]])
    assert results[0]["internalField"] == "parentName"


@patch("app.services.field_matcher.get_field_aliases", return_value=MOCK_ALIASES)
def test_unmapped_unknown_field(mock_aliases):
    from app.services.field_matcher import match_fields
    results = match_fields([MOCK_FIELDS[5]])
    assert results[0]["status"] == "unmapped"
    assert results[0]["internalField"] == ""


@patch("app.services.field_matcher.get_field_aliases", return_value=MOCK_ALIASES)
def test_match_all_fields_returns_same_count(mock_aliases):
    from app.services.field_matcher import match_fields
    results = match_fields(MOCK_FIELDS)
    assert len(results) == len(MOCK_FIELDS)


@patch("app.services.field_matcher.get_field_aliases", return_value=MOCK_ALIASES)
def test_result_has_required_keys(mock_aliases):
    from app.services.field_matcher import match_fields
    results = match_fields(MOCK_FIELDS[:1])
    r = results[0]
    assert "label" in r
    assert "entryId" in r
    assert "internalField" in r
    assert "confidence" in r
    assert "status" in r
