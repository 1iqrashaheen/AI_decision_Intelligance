from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FiniteModel(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)


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
class Kpi(FiniteModel):
    label: str
    value: Optional[float]


class AnalysisResponse(BaseModel):
    dataset_id: str
    kpis: List[Kpi]
    trend: List[Dict[str, Any]]
    by_product: List[Dict[str, Any]]
    findings: List[str]
    source: str = "mock"
    dataset_kind: str = "sales"
    currency: Optional[str] = None
    totals: Dict[str, Any] = Field(default_factory=dict)
    quality: Dict[str, Any] = Field(default_factory=dict)
    anomalies: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    date_range: Optional[Dict[str, str]] = None
    by_country: List[Dict[str, Any]] = Field(default_factory=list)
    by_category: List[Dict[str, Any]] = Field(default_factory=list)
    by_status: List[Dict[str, Any]] = Field(default_factory=list)


# ---------- forecast ----------
class ForecastRequest(BaseModel):
    dataset_id: str
    periods: int = Field(3, ge=1, le=24)


class ForecastResponse(BaseModel):
    dataset_id: str
    method: str
    forecast: List[Dict[str, Any]]
    recommendation: Optional[str] = None
    source: str = "mock"


# ---------- simulate ----------
class Baseline(FiniteModel):
    units: float = Field(..., ge=0)
    price: float = Field(..., ge=0)
    unit_cost: float = Field(..., ge=0)
    marketing: float = Field(0, ge=0)
    expenses: float = Field(0, ge=0)


class Changes(FiniteModel):
    """All values are fractions: 0.10 means +10%."""
    price_pct: float = Field(0, ge=-1, le=5)
    cost_pct: float = Field(0, ge=-1, le=5)
    marketing_pct: float = Field(0, ge=-1, le=5)
    expenses_pct: float = Field(0, ge=-1, le=5)


class Assumptions(FiniteModel):
    elasticity: float = -1.2
    marketing_lift: float = 0.15


class SimulateRequest(BaseModel):
    baseline: Baseline
    changes: Changes
    assumptions: Assumptions = Assumptions()


class Metrics(FiniteModel):
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
    scenario_dataset_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    context_used: List[str]
    source: str = "mock"
    warnings: List[str] = Field(default_factory=list)


# ---------- export ----------
class ReportScenario(FiniteModel):
    name: str = Field(..., min_length=1, max_length=120)
    revenue: Optional[float] = None
    cogs: Optional[float] = None
    profit: Optional[float] = None
    units: Optional[float] = None
    marketing: Optional[float] = None
    expenses: Optional[float] = None
    total_costs: Optional[float] = None
    margin_pct: Optional[float] = None
    changes: Optional[Changes] = None
    assumptions: Optional[Assumptions] = None
    case: str = Field("custom", max_length=30)
    notes: List[str] = Field(default_factory=list, max_length=30)

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        if not value.strip():
            raise ValueError("Enter a scenario name.")
        return value.strip()


class ReportPayload(FiniteModel):
    title: str = Field("Business decision report", min_length=1, max_length=160)
    dataset_id: Optional[str] = Field(None, min_length=1, max_length=128)
    kpis: List[Kpi] = Field(default_factory=list, max_length=100)
    scenarios: List[ReportScenario] = Field(default_factory=list, max_length=12)
    assumptions: List[str] = Field(default_factory=list, max_length=80)
    include_forecast: bool = False
    dataset_name: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=20)
    generated_at: Optional[str] = None
    source: str = "supplied"
    analysis: Optional[AnalysisResponse] = None
    baseline: Optional[ReportScenario] = None
    recommendations: List[str] = Field(default_factory=list)
    forecast: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)
