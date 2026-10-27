import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import INSECURE_DEFAULT_SECRET, SECRET_KEY
from app.db import maybe_init_db
from app.routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    startup()
    yield


app = FastAPI(
    title="Identity-Aware Agent Gateway",
    lifespan=lifespan,
    version="1.0.0",
    description="Identity-shaped policy, retrieval, tools, auditability, and review for AI agent requests.",
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)


def startup():
    if SECRET_KEY == INSECURE_DEFAULT_SECRET:
        logging.getLogger("iaag").warning(
            "IAAG_SECRET_KEY is the insecure default; set a real secret outside local demos."
        )
    maybe_init_db()


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")
