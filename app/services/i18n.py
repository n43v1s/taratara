import json
from pathlib import Path
from functools import lru_cache

SUPPORTED_LANGS = ("en", "id")
DEFAULT_LANG = "en"
I18N_DIR = Path(__file__).parent.parent / "i18n"


@lru_cache(maxsize=None)
def _load(lang: str) -> dict:
    path = I18N_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_lang(request) -> str:
    lang = request.cookies.get("lang", DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def make_t(lang: str):
    strings = _load(lang)

    def t(key: str, params: dict | None = None, **kwargs) -> str:
        parts = key.split(".")
        node = strings
        for part in parts:
            if not isinstance(node, dict):
                return key
            node = node.get(part, key)
        result = node if isinstance(node, str) else key
        for k, v in (params or {}).items():
            result = result.replace("{" + k + "}", str(v))
        for k, v in kwargs.items():
            result = result.replace("{" + k + "}", str(v))
        return result

    return t
