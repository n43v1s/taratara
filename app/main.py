from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routers import form, mapping, config, dryrun, submit, status, logs, help, reset, lang
from app.render import render

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Tara Caraka Ceria", version="0.1.0")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(form.router)
app.include_router(mapping.router)
app.include_router(config.router)
app.include_router(dryrun.router)
app.include_router(submit.router)
app.include_router(status.router)
app.include_router(logs.router)
app.include_router(help.router)
app.include_router(reset.router)
app.include_router(lang.router)


@app.get("/")
async def dashboard(request: Request):
    from app.services.flow_state import get_flow_state
    flow = get_flow_state()
    return render(request, "dashboard.html", {"flow": flow})


@app.get("/health")
async def health():
    return {"status": "ok"}
