import os
from typing import List

from fastapi import APIRouter

from app.core.errors import APIError
from app.core.store import DATASETS
from app.schemas.common import ChatRequest, ChatResponse
from app.services.analytics import compute_analysis

router = APIRouter(tags=["chat"])


def _answer_from_data(question: str, df, scenario=None) -> tuple[str, List[str]]:
    """Grounded analytical Q&A engine that inspects the actual dataset metrics."""
    q = question.lower()
    analysis = compute_analysis(df, "chat_ctx")
    kpis = {k.label.lower(): k.value for k in analysis.kpis}
    top_p = analysis.by_product[0] if analysis.by_product else None
    low_m_p = min(analysis.by_product, key=lambda x: x["gross_margin"]) if analysis.by_product else None

    context = []
    total_rev = kpis.get("total revenue", 0.0)
    net_profit = kpis.get("net profit", 0.0)
    profit_margin = kpis.get("profit margin (%)", 0.0)

    if any(w in q for w in ["best", "highest sale", "top product", "top performing", "most popular"]):
        context.append("by_product.revenue")
        if top_p:
            return (
                f"Your top performing product is '{top_p['product']}' with ${top_p['revenue']:,.2f} in sales, "
                f"accounting for {top_p['share_pct']}% of total business revenue.",
                context,
            )

    if any(w in q for w in ["lowest margin", "worst product", "low margin", "least profitable"]):
        context.append("by_product.gross_margin")
        if low_m_p:
            return (
                f"The product with the lowest gross margin is '{low_m_p['product']}' at {low_m_p['gross_margin']}%. "
                f"Consider reviewing supplier pricing or adjusting unit price.",
                context,
            )

    if any(w in q for w in ["revenue", "sales", "how much revenue", "how much sale"]):
        context.append("kpis.total_revenue")
        return (f"Total revenue across all recorded periods is ${total_rev:,.2f}.", context)

    if any(w in q for w in ["profit", "net profit", "margin", "how profitable"]):
        context.append("kpis.net_profit")
        context.append("kpis.profit_margin")
        status = "running profitably" if net_profit >= 0 else "operating at a loss"
        return (
            f"Net profit is ${net_profit:,.2f} with an overall profit margin of {profit_margin:.1f}%. "
            f"The business is currently {status}.",
            context,
        )

    if any(w in q for w in ["trend", "growth", "month", "seasonality"]):
        context.append("trend.periods")
        if len(analysis.trend) >= 2:
            first, last = analysis.trend[0], analysis.trend[-1]
            diff = last["revenue"] - first["revenue"]
            direction = "increased" if diff >= 0 else "decreased"
            return (
                f"Sales have {direction} from ${first['revenue']:,.2f} in {first['period']} to ${last['revenue']:,.2f} in {last['period']}.",
                context,
            )

    if scenario and any(w in q for w in ["scenario", "what-if", "what if", "change"]):
        context.append("scenario.profit")
        context.append("scenario.revenue")
        d_profit = scenario.delta.get("profit", 0.0)
        d_rev = scenario.delta.get("revenue", 0.0)
        p_sign = "+" if d_profit >= 0 else ""
        return (
            f"In your scenario, projected revenue is ${scenario.scenario.revenue:,.2f} (change: {d_rev:+,.2f}) "
            f"and projected net profit is ${scenario.scenario.profit:,.2f} ({p_sign}${d_profit:,.2f} vs baseline).",
            context,
        )

    if any(w in q for w in ["recommend", "advice", "suggestion", "what should"]):
        context.append("analysis.findings")
        rec = "Focus on protecting margins: "
        if low_m_p:
            rec += f"renegotiate costs for '{low_m_p['product']}' ({low_m_p['gross_margin']}% margin). "
        if top_p:
            rec += f"Ensure adequate inventory for top revenue generator '{top_p['product']}'."
        return (rec, context)

    # General overview
    context.append("kpis.overview")
    return (
        f"Your business generated ${total_rev:,.2f} in total revenue and ${net_profit:,.2f} in net profit ({profit_margin:.1f}% margin). "
        f"Top product is '{top_p['product'] if top_p else 'N/A'}'. Ask me about product margins, sales trends, or what-if scenario impacts!",
        context,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if req.dataset_id not in DATASETS:
        raise APIError(404, "dataset_not_found", f"No dataset with id '{req.dataset_id}'.")

    df = DATASETS[req.dataset_id]

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    if api_key:
        try:
            import httpx
            analysis = compute_analysis(df, req.dataset_id)
            context_summary = (
                f"Business Metrics: Total Revenue=${analysis.kpis[0].value}, Net Profit=${analysis.kpis[3].value}. "
                f"Top Products: {analysis.by_product[:3]}. Findings: {analysis.findings}"
            )
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": f"You are a business decision intelligence assistant. Use this data:\n{context_summary}"},
                        {"role": "user", "content": req.question},
                    ],
                    "temperature": 0.3,
                },
                timeout=10.0,
            )
            if resp.status_code == 200:
                answer = resp.json()["choices"][0]["message"]["content"]
                return ChatResponse(answer=answer, context_used=["llm.openai", "kpis.total_revenue"], source="openai_llm")
        except Exception:
            pass  # Fallback to analytical engine

    answer, ctx = _answer_from_data(req.question, df, req.scenario)
    return ChatResponse(answer=answer, context_used=ctx, source="grounded_assistant")
