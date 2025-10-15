from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .db import init_db
from .routers import health, albums, settings as settings_router, images, events as events_router

app = FastAPI(title="myread", version="0.1.0")

# CORS: allow local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await init_db()


# Routers
app.include_router(health.router, prefix="/api")
app.include_router(albums.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(events_router.router, prefix="/api")

static_path = Path(__file__).parent.parent / "frontend"
print(f"🔧 静态文件路径: {static_path}")
# mount static demo site
try:
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="frontend")
except Exception:
    # ignore if folder missing in some environments
    pass