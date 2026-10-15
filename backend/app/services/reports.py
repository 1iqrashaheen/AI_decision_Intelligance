import csv
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.common import ReportPayload

DISCLAIMER = "These figures are estimates based on stated assumptions, not guaranteed outcomes."

SAMPLE = ReportPayload(
    title="Sample Business Report",
    kpis=[{"label": "Revenue", "value": 100000}, {"label": "Profit", "value": 25000}],
    scenarios=[
        {"name": "Original", "revenue": 100000, "cogs": 60000, "profit": 25000},
        {"name": "Price +10%", "revenue": 96800, "cogs": 52800, "profit": 29000},
    ],
    assumptions=["Price elasticity -1.2", "Marketing lift 0.15"],
)


def build_csv(p: ReportPayload) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([p.title])
    w.writerow([])
    w.writerow(["KPI", "Value"])
    for k in p.kpis:
        w.writerow([k.label, k.value])
    w.writerow([])
    w.writerow(["Scenario", "Revenue", "COGS", "Profit"])
    for s in p.scenarios:
        w.writerow([s.name, s.revenue, s.cogs, s.profit])
    w.writerow([])
    for a in p.assumptions:
        w.writerow(["Assumption", a])
    w.writerow(["Note", DISCLAIMER])
    return buf.getvalue().encode("utf-8")


def _table(data):
    t = Table(data, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def build_pdf(p: ReportPayload) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=p.title)
    st = getSampleStyleSheet()
    story = [Paragraph(p.title, st["Title"]), Spacer(1, 12)]
    if p.kpis:
        story += [Paragraph("Key Metrics", st["Heading2"]),
                  _table([["KPI", "Value"]] + [[k.label, f"{k.value:,.2f}"] for k in p.kpis]), Spacer(1, 12)]
    if p.scenarios:
        rows = [["Scenario", "Revenue", "COGS", "Profit"]] + [
            [s.name, f"{s.revenue:,.2f}", f"{s.cogs:,.2f}", f"{s.profit:,.2f}"] for s in p.scenarios]
        story += [Paragraph("Scenario Comparison", st["Heading2"]), _table(rows), Spacer(1, 12)]
    if p.assumptions:
        story.append(Paragraph("Assumptions", st["Heading2"]))
        story += [Paragraph(f"• {a}", st["Normal"]) for a in p.assumptions]
        story.append(Spacer(1, 12))
    story.append(Paragraph(f"<i>{DISCLAIMER}</i>", st["Normal"]))
    doc.build(story)
    return buf.getvalue()
