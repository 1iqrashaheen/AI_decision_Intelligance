from typing import Literal, Optional

from fastapi import APIRouter, Response

from app.schemas.common import ReportPayload
from app.services import reports

router = APIRouter(tags=["export"])


@router.post("/export")
def export(format: Literal["pdf", "csv"] = "pdf", payload: Optional[ReportPayload] = None):
    """Body optional: with no body, a sample report is returned (Phase 2 starts with sample numbers)."""
    data = payload or reports.SAMPLE
    if format == "csv":
        return Response(reports.build_csv(data), media_type="text/csv",
                        headers={"Content-Disposition": 'attachment; filename="report.csv"'})
    return Response(reports.build_pdf(data), media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="report.pdf"'})
