from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config.settings import get_settings
from app.db.database import init_db
from app.db.repository import mark_productive_day
from app.services.dashboard import build_dashboard_data


APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Focus Day Bot API")
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


class MarkDayRequest(BaseModel):
    user_id: int | None = None
    first_name: str | None = None
    username: str | None = None


@app.on_event("startup")
async def on_startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    settings = get_settings()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "base_url": settings.base_url},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
async def dashboard(
    user_id: int | None = None,
    first_name: str | None = None,
    username: str | None = None,
) -> dict[str, object]:
    return build_dashboard_data(user_id, first_name=first_name, username=username)


@app.post("/api/mark-today")
async def mark_today(payload: MarkDayRequest) -> dict[str, object]:
    if payload.user_id is not None:
        mark_productive_day(
            payload.user_id,
            first_name=payload.first_name,
            username=payload.username,
        )
    return build_dashboard_data(
        payload.user_id,
        first_name=payload.first_name,
        username=payload.username,
    )
