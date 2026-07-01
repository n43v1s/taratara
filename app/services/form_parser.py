import re
import uuid
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone


class FormParseError(Exception):
    pass


async def fetch_form_html(url: str) -> str:
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url)
    if response.status_code != 200:
        raise FormParseError(f"Gagal mengambil form: HTTP {response.status_code}")
    return response.text


def parse_form(html: str, form_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # Extract response URL (form action)
    form_tag = soup.find("form")
    if not form_tag:
        raise FormParseError("Tag <form> tidak ditemukan di halaman ini.")
    response_url = form_tag.get("action", "")

    # Extract form ID from response URL or original URL
    form_id = _extract_form_id(form_url) or _extract_form_id(response_url)

    # Extract fbzx hidden value
    fbzx_tag = soup.find("input", {"name": "fbzx"})
    fbzx = fbzx_tag["value"] if fbzx_tag else ""

    # Extract all fields from the embedded JSON data
    fields = _extract_fields_from_json(html)

    if not fields:
        # Fallback: extract from DOM
        fields = _extract_fields_from_dom(soup)

    if not fields:
        raise FormParseError("Tidak ada field yang berhasil dideteksi dari form ini.")

    ts    = datetime.now()
    short = str(uuid.uuid4())[:6]
    session_id = f"session-{ts.strftime('%Y%m%d-%H%M%S')}-{short}"

    return {
        "sessionId": session_id,
        "sessionLabel": f"Form {ts.strftime('%d %b %Y %H:%M')}",
        "formUrl": form_url,
        "formId": form_id,
        "responseUrl": response_url,
        "fbzx": fbzx,
        "parsedAt": ts.replace(tzinfo=timezone.utc).isoformat(),
        "fields": fields,
        "mappings": {},
    }


def _extract_form_id(url: str) -> str:
    match = re.search(r"/forms/d/e/([a-zA-Z0-9_-]+)/", url)
    if match:
        return match.group(1)
    match = re.search(r"/forms/d/([a-zA-Z0-9_-]+)/", url)
    if match:
        return match.group(1)
    return ""


def _extract_fields_from_json(html: str) -> list[dict]:
    """
    Google Forms embeds field data as FB_PUBLIC_LOAD_DATA_ in the page source.
    We find the variable, then use a bracket counter to extract the full array.
    """
    import json

    marker = re.search(r"FB_PUBLIC_LOAD_DATA_\s*=\s*", html)
    if not marker:
        return []

    start = marker.end()
    if start >= len(html) or html[start] != "[":
        return []

    # Walk forward counting brackets to find the matching closing bracket
    depth = 0
    in_string = False
    escape_next = False
    end = start

    for i, ch in enumerate(html[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    try:
        raw = json.loads(html[start:end])
    except Exception:
        return []

    # Field list is at raw[1][1]
    try:
        field_list = raw[1][1]
    except (IndexError, TypeError):
        return []

    fields = []
    for item in field_list:
        try:
            field = _parse_field_item(item)
            if field:
                fields.append(field)
        except Exception:
            continue

    return fields


def _parse_field_item(item: list) -> dict | None:
    # Structure: [field_id, label, null, type_code, [sub_items], ...]
    # sub_item: [entry_id, options_or_null, ...]
    # options_or_null: [["option_text", ...], ...]
    if not isinstance(item, list) or len(item) < 5:
        return None

    label = item[1] if isinstance(item[1], str) else ""
    label = label.strip()
    field_type_code = item[3] if isinstance(item[3], int) else -1
    sub_items = item[4] if isinstance(item[4], list) else []

    field_type = _resolve_field_type(field_type_code)

    entry_id = ""
    options = []

    for sub in sub_items:
        if not isinstance(sub, list) or not sub:
            continue
        # sub[0] = entry ID (int)
        if isinstance(sub[0], int) and not entry_id:
            entry_id = f"entry.{sub[0]}"
        # sub[1] = list of option tuples [["label", ...], ...]
        if len(sub) > 1 and isinstance(sub[1], list):
            for opt in sub[1]:
                if isinstance(opt, list) and opt and isinstance(opt[0], str):
                    options.append(opt[0])

    if not label or not entry_id:
        return None

    return {
        "label": label,
        "entryId": entry_id,
        "type": field_type,
        "options": options,
    }


def _resolve_field_type(code: int) -> str:
    types = {
        0: "short_text",
        1: "paragraph",
        2: "multiple_choice",
        3: "dropdown",
        4: "checkbox",
        5: "linear_scale",
        7: "grid",
        9: "date",
        10: "time",
    }
    return types.get(code, "unknown")


def _extract_fields_from_dom(soup: BeautifulSoup) -> list[dict]:
    """Fallback: extract entry IDs from input/textarea/select elements in DOM."""
    fields = []
    seen = set()

    for element in soup.find_all(["input", "textarea", "select"]):
        name = element.get("name", "")
        if not name.startswith("entry."):
            continue
        if name in seen:
            continue
        seen.add(name)

        label = ""
        parent = element.find_parent("div")
        if parent:
            label_tag = parent.find(["span", "label", "div"], recursive=True)
            if label_tag:
                label = label_tag.get_text(strip=True)

        fields.append({
            "label": label or name,
            "entryId": name,
            "type": element.name,
            "options": [],
        })

    return fields
