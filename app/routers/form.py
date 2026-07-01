from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from app.services.form_parser import fetch_form_html, parse_form, FormParseError
from app.services.config_handler import save_form_profile
from app.render import render

router = APIRouter(prefix="/form")


@router.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return render(request, "form.html", {
        "result": None,
        "error": None,
    })


@router.post("/parse", response_class=HTMLResponse)
async def parse_form_url(request: Request, url: str = Form(...)):
    url = url.strip()
    is_full_url = url.startswith("https://docs.google.com/forms/")
    is_short_url = url.startswith("https://forms.gle/")
    if not is_full_url and not is_short_url:
        return render(request, "form.html", {
            "result": None,
            "error": "URL harus berupa https://docs.google.com/forms/... atau https://forms.gle/...",
        })

    try:
        html = await fetch_form_html(url)
        profile = parse_form(html, url)
        save_form_profile(profile)
    except FormParseError as e:
        return render(request, "form.html", {
            "result": None,
            "error": str(e),
        })
    except Exception as e:
        return render(request, "form.html", {
            "result": None,
            "error": f"Error tidak terduga: {e}",
        })

    return render(request, "form.html", {
        "result": profile,
        "error": None,
    })
