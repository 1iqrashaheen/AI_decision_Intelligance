from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import CORS_ORIGINS
from backend.app.core.errors import register_error_handlers
from backend.app.routers import analysis, chat, export, simulate, upload, auth, saved
from backend.app.core.database import init_db
from backend.app.core.database import engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from backend.app.core.errors import APIError

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
init_db()


@app.middleware('http')
async def private_api_responses(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

for r in (auth.router, saved.router, upload.router, analysis.router, simulate.router, chat.router, export.router):
    app.include_router(r, prefix="/api")


@app.get("/api/health", tags=["meta"])
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
    except SQLAlchemyError:
        raise APIError(503, 'database_unavailable', 'The database is unavailable.')
    return {
        "status": "ok",
        "database": "connected",
        "module": "07-backend-connections",
        "author": "Muhammad Arham",
        "version": "1.0.0",
    }
