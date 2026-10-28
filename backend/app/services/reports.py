"""Ayesha's comparison reports, using the existing analysis and scenario results."""
import csv
import io
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, KeepTogether

from assistant.ai_assistant import build_evidence
from assistant.data_connection import prepare_business_data
from backend.app.core.store import DATASETS, DATASET_METADATA
from backend.app.schemas.common import ReportPayload, ReportScenario
from backend.app.services.analytics import compute_analysis, compute_forecast, extract_baseline
from backend.app.services.simulator import simulate
from forecasting.integration import published_forecast

DISCLAIMER = "Scenario and forecast figures are estimates based on the stated assumptions, not guaranteed outcomes."
METRICS = [("Units", "units"), ("Revenue", "revenue"), ("Cost of goods", "cogs"),
           ("Marketing", "marketing"), ("Other expenses", "expenses"),
           ("Total costs", "total_costs"), ("Net profit", "profit"), ("Net margin (%)", "margin_pct")]


def prepare_report(payload):
    """Fetch the selected file's results instead of trusting browser totals."""
    if not payload.title.strip():
        raise ValueError("Enter a report title.")
    generated = datetime.now(ZoneInfo("Asia/Karachi")).strftime("%Y-%m-%d %H:%M PKT")
    if not payload.dataset_id:
        if not payload.kpis and not payload.scenarios:
            raise ValueError("Choose a dataset or supply report figures. Empty reports are not available.")
        for scenario in payload.scenarios:
            if scenario.changes is not None or any(getattr(scenario, k) is None for k in ["revenue", "cogs", "profit"]):
                raise ValueError("Supplied scenarios need revenue, cost of goods and profit. Use dataset_id to calculate changes.")
        return payload.model_copy(update={"source": "supplied", "generated_at": generated,
            "analysis": None, "baseline": None, "dataset_name": None, "forecast": None,
            "warnings": ["These figures were supplied with the request and were not checked against an uploaded dataset."]})
    if payload.dataset_id not in DATASETS:
        raise KeyError(payload.dataset_id)
    df = DATASETS[payload.dataset_id]
    analysis = compute_analysis(df, payload.dataset_id)
    a = analysis.model_dump()
    baseline = None
    if analysis.dataset_kind == "sales":
        baseline = ReportScenario(name="Original (actual)", **{k: a["totals"].get(k) for _, k in METRICS})
    scenarios = []
    if payload.scenarios:
        base = extract_baseline(df)
        for requested in payload.scenarios:
            if requested.changes is None or requested.assumptions is None:
                raise ValueError("Each selected scenario needs its changes and assumptions. Saved totals alone are not enough.")
            calculated = simulate(base, requested.changes, requested.assumptions)
            metrics = calculated.scenario.model_dump()
            metrics["total_costs"] = round(metrics["cogs"] + metrics["marketing"] + metrics["expenses"], 2)
            scenarios.append(ReportScenario(name=requested.name, **metrics, changes=requested.changes,
                assumptions=requested.assumptions, case=requested.case, notes=calculated.notes))
    recommendation = build_evidence("What do you recommend?", prepare_business_data(analysis))["recommendations"]["answer"]
    forecast, warnings = None, []
    if payload.include_forecast:
        try:
            forecast = published_forecast(df, payload.dataset_id) or compute_forecast(df, payload.dataset_id).model_dump()
        except ValueError as exc:
            warnings.append(str(exc))
    return ReportPayload(title=payload.title.strip(), dataset_id=payload.dataset_id,
        dataset_name=DATASET_METADATA.get(payload.dataset_id, {}).get("filename", "Uploaded dataset"),
        currency=analysis.currency, generated_at=generated, source="uploaded_data", analysis=analysis,
        kpis=analysis.kpis, baseline=baseline, scenarios=scenarios, recommendations=[recommendation],
        assumptions=["Actual figures come from the selected uploaded file.",
                     "All selected scenarios use the same file and period as the original figures.",
                     "Net profit includes cost of goods, marketing and other expenses when those values are available.",
                     "Scenario demand follows the backend's price elasticity and marketing lift assumptions."],
        forecast=forecast, warnings=warnings)


def _csv_cell(value):
    # Excel treats these prefixes as formulas, even inside a quoted CSV cell.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return "Unavailable" if value is None else value


def build_csv(p):
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)

    def row(*values):
        writer.writerow([_csv_cell(v) for v in values])

    row(p.title)
    row("Generated", p.generated_at)
    row("Source", "Uploaded dataset" if p.source == "uploaded_data" else "Supplied report figures")
    if p.dataset_id:
        row("Dataset", p.dataset_name)
        row("Dataset ID", p.dataset_id)
    row("Currency", p.currency or "Unspecified; no currency conversion applied")
    if p.analysis and p.analysis.date_range:
        row("Recorded dates", p.analysis.date_range["start"], p.analysis.date_range["end"])
    row()
    row("Actual business results" if p.source == "uploaded_data" else "Supplied business results")
    row("KPI", "Value")
    for item in p.kpis:
        row(item.label, item.value)
    row()
    row("Scenario", "Type", *[label for label, _ in METRICS], "Profit change", "Profit change (%)")
    columns = ([p.baseline] if p.baseline else []) + p.scenarios
    for item in columns:
        delta = (round(item.profit - p.baseline.profit, 2) if p.baseline and item.profit is not None and p.baseline.profit is not None else None)
        pct = (round(delta / abs(p.baseline.profit) * 100, 2) if delta is not None and p.baseline.profit else None)
        row(item.name, "Actual" if item is p.baseline else "Estimate",
            *[getattr(item, key) for _, key in METRICS], delta, pct)
    if p.analysis:
        a = p.analysis
        for heading, entries in [("Monthly results", a.trend), ("Product results", a.by_product),
                                 ("Country results", a.by_country), ("Expense categories", a.by_category),
                                 ("Expense statuses", a.by_status)]:
            if not entries:
                continue
            row(); row(heading)
            keys = list(dict.fromkeys(k for entry in entries for k in entry))
            row(*keys)
            for entry in entries:
                row(*[entry.get(k) for k in keys])
        row(); row("Findings")
        for finding in a.findings:
            row(finding)
        row(); row("Data quality", "Value")
        for key, value in a.quality.items():
            row(key.replace("_", " "), value)
        for limitation in a.limitations:
            row("Data note", limitation)
        row("Unusual values flagged", a.anomalies.get("count"))
    row(); row("Points to review")
    for text in p.recommendations:
        row(text)
    row(); row("Scenario inputs and risks")
    for item in p.scenarios:
        if item.changes:
            row(item.name, "Case", item.case)
            row("Input", "Change (%)")
            for key, value in item.changes.model_dump().items():
                row(key.replace("_pct", "").replace("_", " "), round(value * 100, 2))
        if item.assumptions:
            row("Price elasticity", item.assumptions.elasticity)
            row("Marketing lift", item.assumptions.marketing_lift)
        for note in item.notes:
            row("Risk", note)
    if p.forecast:
        row(); row("Forecast estimates", p.forecast["method"])
        row("Period", "Estimated revenue")
        for estimate in p.forecast["forecast"]:
            row(estimate["period"], estimate["revenue"])
        row("Forecast note", p.forecast.get("recommendation"))
    for assumption in p.assumptions:
        row("Assumption", assumption)
    for warning in p.warnings:
        row("Note", warning)
    row("Note", DISCLAIMER)
    return buf.getvalue().encode("utf-8")


def build_pdf(p):
    font_dir = Path(reportlab.__file__).parent / "fonts"
    for name, filename in [("ReportBody", "Vera.ttf"), ("ReportBold", "VeraBd.ttf")]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    styles = getSampleStyleSheet()
    body = ParagraphStyle("ReportBodyStyle", parent=styles["Normal"], fontName="ReportBody", fontSize=8.5, leading=12, spaceAfter=5)
    heading = ParagraphStyle("ReportHeading", parent=body, fontName="ReportBold", fontSize=12, leading=16, spaceBefore=12, spaceAfter=7, keepWithNext=True)
    title = ParagraphStyle("ReportTitle", parent=heading, fontSize=20, leading=25, spaceBefore=0, spaceAfter=12)
    header = ParagraphStyle("ReportHeader", parent=body, fontName="ReportBold", fontSize=8, leading=11, textColor=colors.white)
    number = ParagraphStyle("ReportNumber", parent=body, fontSize=8, leading=11, alignment=TA_RIGHT)
    small = ParagraphStyle("ReportSmall", parent=body, fontSize=7.5, leading=10, textColor=colors.HexColor("#596579"))
    width = A4[0] - 72

    def para(value, style=body):
        return Paragraph(escape(str(value)), style)

    def formatted(value):
        return "Unavailable" if value is None else f"{value:,.2f}"

    def table(rows, widths):
        cells = [[para(v, header if i == 0 else body if j == 0 else number) for j, v in enumerate(r)] for i, r in enumerate(rows)]
        result = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
        result.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#253e68")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f3f6fb"), colors.white]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#d6dfed")),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return result

    story = [para("DECISION AI | BUSINESS REPORT", small), para(p.title, title)]
    for label, value in [("Prepared", p.generated_at), ("Dataset", p.dataset_name),
                         ("Currency", p.currency or "Unspecified; no currency conversion applied")]:
        if value:
            story.append(para(f"{label}: {value}"))
    if p.analysis and p.analysis.date_range:
        dates = p.analysis.date_range
        story.append(para(f"Recorded dates: {dates['start']} to {dates['end']}"))
    if p.source != "uploaded_data":
        story.append(para("Supplied report figures - not checked against an uploaded dataset.", small))
    if p.kpis:
        story += [para("Business results", heading), table([["Metric", "Value"]] + [[k.label, formatted(k.value)] for k in p.kpis], [width * .68, width * .32])]
    if p.analysis:
        story.append(para("Findings", heading))
        for finding in p.analysis.findings:
            story.append(para(finding))
    if p.scenarios:
        story.append(para("Scenario comparison", heading))
        story.append(para("The original column shows recorded results. Other columns show estimates. Values use the currency noted above.", small))
        for start in range(0, len(p.scenarios), 3):
            group = ([p.baseline] if p.baseline else []) + p.scenarios[start:start + 3]
            rows = [["Metric"] + [s.name for s in group]]
            rows += [[label] + [formatted(getattr(s, key)) for s in group] for label, key in METRICS]
            if p.baseline and p.baseline.profit is not None:
                rows.append(["Profit change"] + [formatted(s.profit - p.baseline.profit) if s.profit is not None else "Unavailable" for s in group])
            story += [table(rows, [112] + [(width - 112) / len(group)] * len(group)), Spacer(1, 10)]
    if p.analysis:
        a = p.analysis
        entries = a.by_category if a.dataset_kind == "expenses" else a.by_product
        if entries:
            keys = (["category", "amount", "share_pct"] if a.dataset_kind == "expenses" else
                    ["product", "stock", "inventory_cost_value"] if a.dataset_kind == "inventory" else ["product", "revenue", "gross_margin"])
            rows = [[k.replace("_", " ").title() for k in keys]]
            for entry in entries[:10]:
                rows.append([str(entry.get(keys[0], ""))] + [formatted(entry.get(k)) for k in keys[1:]])
            story += [para("Category results" if a.dataset_kind == "expenses" else "Product results", heading),
                      table(rows, [width * .5, width * .25, width * .25]),
                      para("Showing up to 10 records here. The CSV download includes the full results. Margin and share values are percentages.", small)]
        if a.trend:
            key = "amount" if a.dataset_kind == "expenses" else "revenue"
            rows = [["Period", key.title()]] + [[r["period"], formatted(r.get(key))] for r in a.trend[:12]]
            story += [para("Monthly results", heading), table(rows, [width * .5] * 2)]
            if len(a.trend) > 12:
                story.append(para("Showing the first 12 recorded months. The CSV includes every recorded month.", small))
    if p.recommendations:
        story.append(para("Points to review", heading))
        story += [para(text) for text in p.recommendations]
    if p.scenarios:
        story.append(para("Scenario inputs and risks", heading))
        for item in p.scenarios:
            intro = [para(f"{item.name} ({item.case})", heading)]
            if item.changes:
                labels = {"price_pct": "Price", "cost_pct": "Unit cost", "marketing_pct": "Marketing", "expenses_pct": "Other expenses"}
                intro.append(para("; ".join(f"{labels[key]}: {value * 100:+.2f}%" for key, value in item.changes.model_dump().items())))
            if item.assumptions:
                intro.append(para(f"Price elasticity: {item.assumptions.elasticity:g}; marketing lift: {item.assumptions.marketing_lift:g}."))
            story.append(KeepTogether(intro))
            story += [para(note) for note in item.notes]
    if p.forecast:
        rows = [["Period", "Estimated revenue"]] + [[r["period"], formatted(r["revenue"])] for r in p.forecast["forecast"]]
        story += [para("Forecast estimates", heading), para("Method: " + p.forecast["method"]), table(rows, [width * .5] * 2)]
        if p.forecast.get("recommendation"):
            story.append(para(p.forecast["recommendation"]))
    if p.analysis:
        a = p.analysis
        story.append(para("Data coverage", heading))
        story.append(para("; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in a.quality.items())))
        story.append(para(f"Unusual values flagged: {a.anomalies.get('count', 0)}. Flagged values remain in the analysis."))
        story += [para(text) for text in a.limitations]
    story.append(para("Assumptions and notes", heading))
    story += [para(text) for text in p.assumptions + p.warnings]
    story.append(para(DISCLAIMER))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("ReportBody", 7)
        canvas.setFillColor(colors.HexColor("#596579"))
        canvas.drawString(36, 23, "DecisionAI | Actual figures and estimates are labeled separately")
        canvas.drawRightString(A4[0] - 36, 23, str(doc.page))
        canvas.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=p.title, author="AI Decision Intelligence team",
                           leftMargin=36, rightMargin=36, topMargin=32, bottomMargin=42)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
