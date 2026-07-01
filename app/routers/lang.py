from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.services.i18n import SUPPORTED_LANGS, DEFAULT_LANG

router = APIRouter(prefix="/lang")


@router.post("/set")
async def set_lang(request: Request):
    form = await request.form()
    lang = form.get("lang", DEFAULT_LANG)
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    referer = request.headers.get("referer", "/")
    response = RedirectResponse(url=referer, status_code=303)
    response.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, httponly=True)
    return response
