from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import CORS_ORIGINS
from backend.app.core.errors import register_error_handlers
from backend.app.routers import analysis, chat, export, simulate, upload

app = FastAPI(
    title="AI Decision Intelligence & Simulator API",
    description="Backend integration APIs connecting upload, analysis, simulation, chat, and reporting.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

for r in (upload.router, analysis.router, simulate.router, chat.router, export.router):
    app.include_router(r, prefix="/api")


@app.get("/api/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "module": "07-backend-connections",
        "author": "Muhammad Arham",
        "version": "1.0.0",
    }
