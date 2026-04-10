from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db import maybe_init_db
from app.routes import router

app = FastAPI(
    title="Identity-Aware Agent Gateway",
    version="1.0.0",
    description="Identity-shaped policy, retrieval, tools, auditability, and review for AI agent requests.",
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)


@app.on_event("startup")
def startup():
    maybe_init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
