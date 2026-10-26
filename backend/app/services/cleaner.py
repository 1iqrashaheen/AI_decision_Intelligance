"""Data cleaning and column mapping pipeline for uploaded datasets.
Supports standard sales CSV/Excel files and UCI Online Retail II datasets.
"""
from typing import Any, Dict, List, Optional, Tuple
import re
import numpy as np
import pandas as pd

from app.schemas.common import ColumnInfo, QualityReport

ALIASES = {
    "date": ["invoicedate", "date", "month", "period", "order_date", "timestamp", "time"],
    "product": ["description", "stockcode", "product", "item", "sku", "product_name", "name"],
    "units": ["quantity", "units", "qty", "units_sold", "sold", "volume"],
    "price": ["price", "unit_price", "selling_price", "sale_price"],
    "unit_cost": ["unit_cost", "cost", "cogs", "cost_price", "unit_cogs"],
    "marketing_spend": ["marketing_spend", "marketing", "ad_spend", "marketing_budget", "ads"],
    "expenses": ["expenses", "expense", "other_expenses", "operating_expenses", "opex", "overhead"],
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def detect_mapping(columns: List[str]) -> Dict[str, Optional[str]]:
    mapping: Dict[str, Optional[str]] = {}
    used = set()
    norm_cols = {c: _norm(c) for c in columns}

    for field, aliases in ALIASES.items():
        matched = None
        for col, ncol in norm_cols.items():
            if col not in used and ncol in aliases:
                matched = col
                used.add(col)
                break
        mapping[field] = matched

    return mapping


def clean_dataframe(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, QualityReport, Dict[str, Any]]:
    """Cleans raw uploaded DataFrame and returns (clean_df, quality_report, metadata)."""
    raw_df = raw_df.copy()
    initial_rows = len(raw_df)
    initial_cols = len(raw_df.columns)
    duplicate_rows = int(raw_df.duplicated().sum())
    missing_cells = int(raw_df.isna().sum().sum())

    # Raw columns info
    columns_info = [
        ColumnInfo(name=str(c), dtype=str(raw_df[c].dtype), missing=int(raw_df[c].isna().sum()))
        for c in raw_df.columns
    ]

    mapping = detect_mapping(list(raw_df.columns))

    # Check for Online Retail II cancellation invoices (starts with 'C')
    cancelled_count = 0
    invoice_col = next((c for c in raw_df.columns if _norm(c) in ["invoice", "invoiceno", "invoice_no"]), None)
    if invoice_col:
        cancel_mask = raw_df[invoice_col].astype(str).str.strip().str.upper().str.startswith("C")
        cancelled_count = int(cancel_mask.sum())
        raw_df = raw_df[~cancel_mask]

    # Required core fields
    date_col = mapping.get("date")
    product_col = mapping.get("product")
    units_col = mapping.get("units")
    price_col = mapping.get("price")
    cost_col = mapping.get("unit_cost")
    mkt_col = mapping.get("marketing_spend")
    exp_col = mapping.get("expenses")

    if not date_col or not product_col:
        # Fallback to first two object/string columns if possible
        obj_cols = [c for c in raw_df.columns if raw_df[c].dtype == object]
        date_col = date_col or (obj_cols[0] if len(obj_cols) > 0 else raw_df.columns[0])
        product_col = product_col or (obj_cols[1] if len(obj_cols) > 1 else raw_df.columns[1])

    # Standardize records
    clean_records = []
    dropped_missing = 0
    dropped_invalid = 0

    for _, row in raw_df.iterrows():
        # Date parsing
        d_val = row.get(date_col)
        if pd.isna(d_val) or str(d_val).strip() == "":
            dropped_missing += 1
            continue

        try:
            dt = pd.to_datetime(d_val, errors="coerce")
            if pd.isna(dt):
                dropped_invalid += 1
                continue
            date_str = dt.strftime("%Y-%m-%d")
            month_str = dt.strftime("%Y-%m")
        except Exception:
            dropped_invalid += 1
            continue

        # Product description
        p_val = str(row.get(product_col, "")).strip()
        if not p_val or p_val.lower() == "nan":
            dropped_missing += 1
            continue

        # Units
        u_raw = row.get(units_col, 1) if units_col else 1
        try:
            u_clean = float(re.sub(r"[^\d.-]", "", str(u_raw))) if pd.notna(u_raw) else 0.0
            if u_clean <= 0:
                dropped_invalid += 1
                continue
        except Exception:
            dropped_invalid += 1
            continue

        # Price
        pr_raw = row.get(price_col, 0.0) if price_col else 0.0
        try:
            pr_clean = float(re.sub(r"[^\d.-]", "", str(pr_raw))) if pd.notna(pr_raw) else 0.0
            if pr_clean < 0:
                dropped_invalid += 1
                continue
        except Exception:
            dropped_invalid += 1
            continue

        # Unit cost (if not provided, default to 60% of unit price as in what-if model)
        if cost_col and pd.notna(row.get(cost_col)):
            try:
                c_clean = float(re.sub(r"[^\d.-]", "", str(row[cost_col])))
            except Exception:
                c_clean = round(pr_clean * 0.60, 2)
        else:
            c_clean = round(pr_clean * 0.60, 2)

        # Marketing spend
        if mkt_col and pd.notna(row.get(mkt_col)):
            try:
                m_clean = float(re.sub(r"[^\d.-]", "", str(row[mkt_col])))
            except Exception:
                m_clean = 0.0
        else:
            m_clean = 0.0

        # Expenses
        if exp_col and pd.notna(row.get(exp_col)):
            try:
                e_clean = float(re.sub(r"[^\d.-]", "", str(row[exp_col])))
            except Exception:
                e_clean = 0.0
        else:
            e_clean = 0.0

        rev = round(u_clean * pr_clean, 2)
        cogs = round(u_clean * c_clean, 2)
        profit = round(rev - cogs - m_clean - e_clean, 2)

        clean_records.append({
            "date": date_str,
            "month": month_str,
            "product": p_val,
            "units": u_clean,
            "price": pr_clean,
            "unit_cost": c_clean,
            "marketing_spend": m_clean,
            "expenses": e_clean,
            "revenue": rev,
            "cogs": cogs,
            "profit": profit,
        })

    clean_df = pd.DataFrame(clean_records)

    quality = QualityReport(
        rows=len(clean_df),
        columns=initial_cols,
        duplicate_rows=duplicate_rows,
        missing_cells=missing_cells,
        columns_info=columns_info,
    )

    metadata = {
        "initial_rows": initial_rows,
        "clean_rows": len(clean_df),
        "cancelled_orders_removed": cancelled_count,
        "dropped_missing": dropped_missing,
        "dropped_invalid": dropped_invalid,
        "mapping": mapping,
    }

    return clean_df, quality, metadata
