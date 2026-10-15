from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------- upload ----------
class ColumnInfo(BaseModel):
    name: str
    dtype: str
    missing: int


class QualityReport(BaseModel):
    rows: int
    columns: int
    duplicate_rows: int
    missing_cells: int
    columns_info: List[ColumnInfo]


class UploadResponse(BaseModel):
    dataset_id: str
    filename: str
    quality: QualityReport
    preview: List[Dict[str, Any]]


# ---------- analysis ----------
class Kpi(BaseModel):
    label: str
    value: float


class AnalysisResponse(BaseModel):
    dataset_id: str
    kpis: List[Kpi]
    trend: List[Dict[str, Any]]
    by_product: List[Dict[str, Any]]
    findings: List[str]
    source: str = "mock"


# ---------- forecast ----------
class ForecastRequest(BaseModel):
    dataset_id: str
    periods: int = Field(3, ge=1, le=24)


class ForecastResponse(BaseModel):
    dataset_id: str
    method: str
    forecast: List[Dict[str, Any]]
    source: str = "mock"


# ---------- simulate ----------
class Baseline(BaseModel):
    units: float = Field(..., ge=0)
    price: float = Field(..., ge=0)
    unit_cost: float = Field(..., ge=0)
    marketing: float = Field(0, ge=0)
    expenses: float = Field(0, ge=0)


class Changes(BaseModel):
    """All values are fractions: 0.10 means +10%."""
    price_pct: float = Field(0, ge=-1, le=5)
    cost_pct: float = Field(0, ge=-1, le=5)
    marketing_pct: float = Field(0, ge=-1, le=5)
    expenses_pct: float = Field(0, ge=-1, le=5)


class Assumptions(BaseModel):
    elasticity: float = -1.2
    marketing_lift: float = 0.15


class SimulateRequest(BaseModel):
    baseline: Baseline
    changes: Changes
    assumptions: Assumptions = Assumptions()


class Metrics(BaseModel):
    units: float
    revenue: float
    cogs: float
    marketing: float
    expenses: float
    profit: float
    margin_pct: float


class SimulateResponse(BaseModel):
    original: Metrics
    scenario: Metrics
    delta: Dict[str, float]
    assumptions: Assumptions
    notes: List[str]


class CaseResult(BaseModel):
    case: str
    assumptions: Assumptions
    result: SimulateResponse


class CompareResponse(BaseModel):
    cases: List[CaseResult]


# ---------- chat ----------
class ChatRequest(BaseModel):
    dataset_id: str
    question: str = Field(..., min_length=1, max_length=1000)
    scenario: Optional[SimulateResponse] = None


class ChatResponse(BaseModel):
    answer: str
    context_used: List[str]
    source: str = "mock"


# ---------- export ----------
class ReportScenario(BaseModel):
    name: str
    revenue: float
    cogs: float
    profit: float


class ReportPayload(BaseModel):
    title: str = "Business Report"
    kpis: List[Kpi] = []
    scenarios: List[ReportScenario] = []
    assumptions: List[str] = []
