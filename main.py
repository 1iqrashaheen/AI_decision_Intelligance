"""Run from the repository root: python -m uvicorn main:app --port 8001."""
from pathlib import Path

from dotenv import load_dotenv
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

from backend.app.main import app

# Only serve website files; keep .env and the rest of the project private.
app.mount("/css", StaticFiles(directory=ROOT / "css"), name="css")
app.mount("/js", StaticFiles(directory=ROOT / "js"), name="js")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "index.html")


@app.get("/data/sample_sales.csv", include_in_schema=False)
def sample_sales():
    return FileResponse(ROOT / "data" / "sample_sales.csv", media_type="text/csv")


def page_endpoint(filename):
    def serve():
        return FileResponse(ROOT / filename)
    return serve


for filename in ["index.html", "upload.html", "whatif.html", "compare.html", "assistant.html"]:
    app.add_api_route("/" + filename, page_endpoint(filename), methods=["GET"], include_in_schema=False)
