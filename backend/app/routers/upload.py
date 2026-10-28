import io
import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, UploadFile

from backend.app.core.config import ALLOWED_EXT, MAX_UPLOAD_MB
from backend.app.core.errors import APIError
from backend.app.core.store import save_dataset
from backend.app.schemas.common import ColumnInfo, QualityReport, UploadResponse
from backend.app.services.cleaner import clean_dataframe

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    name = file.filename or "upload"
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise APIError(400, "invalid_file_type", f"Only {', '.join(sorted(ALLOWED_EXT))} files are allowed.")

    raw = await file.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(raw) == 0:
        raise APIError(422, "empty_file", "The uploaded file is empty.")
    if len(raw) > MAX_UPLOAD_MB * 1024 * 1024:
        raise APIError(413, "file_too_large", f"File exceeds {MAX_UPLOAD_MB} MB.")

    try:
        raw_df = pd.read_csv(io.BytesIO(raw)) if ext == ".csv" else pd.read_excel(io.BytesIO(raw))
    except Exception:
        raise APIError(422, "unreadable_file", "The file could not be read as a table.")

    if raw_df.empty or len(raw_df.columns) == 0:
        raise APIError(422, "empty_file", "The file contains no data rows.")

    try:
        clean_df, quality, meta = clean_dataframe(raw_df)
    except ValueError as exc:
        raise APIError(422, "invalid_dataset", str(exc)) from exc
    if clean_df.empty:
        raise APIError(422, "empty_file", "The file contains no usable data rows after cleaning.")

    dataset_id = save_dataset(clean_df, meta={"filename": name, "quality": quality.model_dump(), **meta})

    preview = json.loads(clean_df.head(10).to_json(orient="records", date_format="iso"))
    return UploadResponse(dataset_id=dataset_id, filename=name, quality=quality, preview=preview)
