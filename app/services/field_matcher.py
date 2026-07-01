import re
from rapidfuzz import fuzz
from app.services.config_handler import get_field_aliases

CONFIDENCE_AUTO = 90
CONFIDENCE_SUGGEST = 75

INTERNAL_FIELDS = [
    "childName", "birthInfo", "childAge", "gender", "religion",
    "parentName", "satker", "phoneNumber", "address", "allergy", "bookingDates",
]


def normalize(label: str) -> str:
    label = label.lower().strip()
    label = re.sub(r"\s+", " ", label)
    label = re.sub(r"[^\w\s]", "", label)
    return label


def match_fields(parsed_fields: list[dict]) -> list[dict]:
    """
    Match each parsed field to an internal field.
    Returns list of match results with confidence and status.
    """
    aliases = get_field_aliases()
    normalized_aliases: dict[str, list[str]] = {
        internal: [normalize(a) for a in alias_list]
        for internal, alias_list in aliases.items()
    }

    results = []
    for field in parsed_fields:
        label = field["label"]
        norm_label = normalize(label)
        match = _find_best_match(norm_label, normalized_aliases)
        results.append({
            "label": label,
            "entryId": field["entryId"],
            "type": field["type"],
            "options": field["options"],
            "internalField": match["internalField"],
            "confidence": match["confidence"],
            "status": match["status"],
        })

    return results


def _find_best_match(norm_label: str, normalized_aliases: dict) -> dict:
    # Layer 1: exact alias match
    for internal, aliases in normalized_aliases.items():
        if norm_label in aliases:
            return {"internalField": internal, "confidence": 100, "status": "auto"}

    # Layer 2: fuzzy match — find best score across all aliases of all internal fields
    best_score = 0
    best_internal = ""

    for internal, aliases in normalized_aliases.items():
        for alias in aliases:
            score = fuzz.token_sort_ratio(norm_label, alias)
            if score > best_score:
                best_score = score
                best_internal = internal

    if best_score >= CONFIDENCE_AUTO:
        return {"internalField": best_internal, "confidence": best_score, "status": "auto"}
    elif best_score >= CONFIDENCE_SUGGEST:
        return {"internalField": best_internal, "confidence": best_score, "status": "suggest"}
    else:
        return {"internalField": "", "confidence": best_score, "status": "unmapped"}
