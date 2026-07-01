"""Tests for form_parser service."""
import pytest
from app.services.form_parser import parse_form, _extract_form_id, FormParseError

# Minimal Google Form HTML fixture with FB_PUBLIC_LOAD_DATA_
FIXTURE_HTML = """
<html><body>
<form action="https://docs.google.com/forms/d/e/FORM_ID_123/formResponse">
<input name="fbzx" value="-999">
</form>
<script>
var FB_PUBLIC_LOAD_DATA_ = [null,["Judul Form",[[1001,"Nama Anak",null,0,[[111111,null,0]],null,null,null,null,null,null,[null,"Nama Anak"]],[1002,"Jenis Kelamin",null,4,[[222222,[["Laki - Laki",null,null,null,0],["Perempuan",null,null,null,0]],0]],null,null,null,null,null,null,[null,"Jenis Kelamin"]],[1003,"Tanggal Booking",null,4,[[333333,[["01 Juli",null,null,null,0],["02 Juli",null,null,null,0]],0]],null,null,null,null,null,null,[null,"Tanggal Booking"]]]]];
</script>
</body></html>
"""

FORM_URL = "https://docs.google.com/forms/d/e/FORM_ID_123/viewform"


def test_parse_form_returns_required_keys():
    result = parse_form(FIXTURE_HTML, FORM_URL)
    assert "formId" in result
    assert "responseUrl" in result
    assert "fbzx" in result
    assert "fields" in result
    assert "parsedAt" in result


def test_parse_form_detects_fields():
    result = parse_form(FIXTURE_HTML, FORM_URL)
    assert len(result["fields"]) == 3


def test_parse_form_field_labels():
    result = parse_form(FIXTURE_HTML, FORM_URL)
    labels = [f["label"] for f in result["fields"]]
    assert "Nama Anak" in labels
    assert "Jenis Kelamin" in labels
    assert "Tanggal Booking" in labels


def test_parse_form_field_entry_ids():
    result = parse_form(FIXTURE_HTML, FORM_URL)
    entry_ids = [f["entryId"] for f in result["fields"]]
    assert "entry.111111" in entry_ids
    assert "entry.222222" in entry_ids
    assert "entry.333333" in entry_ids


def test_parse_form_options():
    result = parse_form(FIXTURE_HTML, FORM_URL)
    gender_field = next(f for f in result["fields"] if f["label"] == "Jenis Kelamin")
    assert "Laki - Laki" in gender_field["options"]
    assert "Perempuan" in gender_field["options"]

    booking_field = next(f for f in result["fields"] if f["label"] == "Tanggal Booking")
    assert "01 Juli" in booking_field["options"]
    assert "02 Juli" in booking_field["options"]


def test_parse_form_field_types():
    result = parse_form(FIXTURE_HTML, FORM_URL)
    text_field = next(f for f in result["fields"] if f["label"] == "Nama Anak")
    assert text_field["type"] == "short_text"

    checkbox_field = next(f for f in result["fields"] if f["label"] == "Jenis Kelamin")
    assert checkbox_field["type"] == "checkbox"


def test_parse_form_response_url():
    result = parse_form(FIXTURE_HTML, FORM_URL)
    assert "formResponse" in result["responseUrl"]


def test_parse_form_fbzx():
    result = parse_form(FIXTURE_HTML, FORM_URL)
    assert result["fbzx"] == "-999"


def test_parse_form_no_form_tag():
    with pytest.raises(FormParseError, match="Tag <form>"):
        parse_form("<html><body>no form here</body></html>", FORM_URL)


def test_extract_form_id_full_url():
    url = "https://docs.google.com/forms/d/e/1FAIpQLSabc123/viewform"
    assert _extract_form_id(url) == "1FAIpQLSabc123"


def test_extract_form_id_empty():
    assert _extract_form_id("https://example.com") == ""
