from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.core.errors import register_error_handlers
from app.routers import analysis, chat, export, simulate, upload

app = FastAPI(title="AI Decision Intelligence API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
register_error_handlers(app)

for r in (upload.router, analysis.router, simulate.router, chat.router, export.router):
    app.include_router(r, prefix="/api")


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok"}
