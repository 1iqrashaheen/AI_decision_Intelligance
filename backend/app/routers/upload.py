import io
import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, UploadFile

from app.core.config import ALLOWED_EXT, MAX_UPLOAD_MB
from app.core.errors import APIError
from app.core.store import save_dataset
from app.schemas.common import ColumnInfo, QualityReport, UploadResponse

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    name = file.filename or "upload"
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise APIError(400, "invalid_file_type", f"Only {', '.join(sorted(ALLOWED_EXT))} files are allowed.")
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_MB * 1024 * 1024:
        raise APIError(413, "file_too_large", f"File exceeds {MAX_UPLOAD_MB} MB.")
    try:
        df = pd.read_csv(io.BytesIO(raw)) if ext == ".csv" else pd.read_excel(io.BytesIO(raw))
    except Exception:
        raise APIError(422, "unreadable_file", "The file could not be read as a table.")
    if df.empty or len(df.columns) == 0:
        raise APIError(422, "empty_file", "The file contains no data rows.")

    quality = QualityReport(
        rows=len(df), columns=len(df.columns),
        duplicate_rows=int(df.duplicated().sum()),
        missing_cells=int(df.isna().sum().sum()),
        columns_info=[ColumnInfo(name=str(c), dtype=str(df[c].dtype), missing=int(df[c].isna().sum())) for c in df.columns],
    )
    preview = json.loads(df.head(10).to_json(orient="records", date_format="iso"))
    return UploadResponse(dataset_id=save_dataset(df), filename=name, quality=quality, preview=preview)
