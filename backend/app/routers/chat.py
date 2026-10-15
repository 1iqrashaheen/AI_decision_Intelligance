from fastapi import APIRouter

from app.core.errors import APIError
from app.core.store import DATASETS
from app.schemas.common import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if req.dataset_id not in DATASETS:
        raise APIError(404, "dataset_not_found", f"No dataset with id '{req.dataset_id}'.")
    # MOCK: replace with Iqra's LLM module (pass only computed results as context)
    return ChatResponse(answer="Mock answer: product B has the lowest profit margin.",
                        context_used=["by_product.margin_pct"])
