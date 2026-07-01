from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.render import render

router    = APIRouter(prefix="/help")


@router.get("/", response_class=HTMLResponse)
async def help_page(request: Request):
    return render(request, "help.html", {})
