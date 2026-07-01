from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.services.i18n import get_lang, make_t

_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def render(request, template_name: str, context: dict | None = None) -> HTMLResponse:
    lang = get_lang(request)
    ctx = {"lang": lang, "t": make_t(lang)}
    ctx.update(context or {})
    return _templates.TemplateResponse(request=request, name=template_name, context=ctx)
