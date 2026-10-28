from typing import Literal

from fastapi import APIRouter, Response

from backend.app.core.errors import APIError
from backend.app.schemas.common import ReportPayload
from backend.app.services import reports

router = APIRouter(tags=["export"])


@router.post("/export")
def export(payload: ReportPayload, format: Literal["pdf", "csv"] = "pdf"):
    """Download results for the selected file, or clearly labeled supplied figures."""
    try:
        data = reports.prepare_report(payload)
    except KeyError as exc:
        raise APIError(404, "dataset_not_found", "The selected dataset is unavailable. Upload it again after a server restart.") from exc
    except ValueError as exc:
        raise APIError(422, "invalid_report", str(exc)) from exc
    content = reports.build_csv(data) if format == "csv" else reports.build_pdf(data)
    return Response(content, media_type="text/csv; charset=utf-8" if format == "csv" else "application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="decisionai-report.{format}"'})
