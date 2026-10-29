"""Calculate business results from the supplied data.

A percentage of 25 means 25%. UCI retail values are in GBP; other files
need their currency supplied if it is known.
"""
import re

import numpy as np
import pandas as pd


ALIASES = {
    "invoice": "invoice_no", "invoiceno": "invoice_no",
    "stockcode": "stock_code", "invoicedate": "date", "invoice_date": "date",
    "order_date": "date", "quantity": "units", "qty": "units",
    "units_sold": "units", "unitprice": "price", "unit_price": "price",
    "selling_price": "price", "product_name": "product", "item": "product",
    "marketing": "marketing_spend", "ad_spend": "marketing_spend",
    "operating_expenses": "expenses", "other_expenses": "expenses",
    "customerid": "customer_id", "name": "product", "cost": "unit_cost",
}


def _number(value):
    return round(float(value), 2) if pd.notna(value) and np.isfinite(value) else None


def _pct(part, whole):
    return _number(part / whole * 100) if whole else None


def _records(frame):
    # pandas serializes NaN to JSON null and numpy scalars to ordinary numbers.
    import json
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def prepare_dataframe(raw, kind="auto"):
    """Read the team's column names and count rows that cannot be used.

    Keep returns and leave missing costs blank. Samad's preprocessing still
    handles the original datasets before they reach this function.
    """
    if not isinstance(raw, pd.DataFrame) or raw.empty:
        raise ValueError("Provide a non-empty dataframe.")
    df = raw.copy()
    names = [re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_") for c in df]
    df.columns = [ALIASES.get(c, c) for c in names]
    if df.columns.duplicated().any():
        raise ValueError("Ambiguous columns: more than one column maps to the same field.")
    if kind == "auto":
        if {"amount", "category"} <= set(df):
            kind = "expenses"
        elif {"stock", "price", "unit_cost"} <= set(df):
            kind = "inventory"
        else:
            kind = "sales"
    required = {
        "sales": ["date", "units", "price"],
        "expenses": ["date", "amount", "category"],
        "inventory": ["product", "price", "unit_cost", "stock"],
    }
    if kind not in required:
        raise ValueError("kind must be sales, expenses, inventory, or auto.")
    if kind == "sales":
        if "stock_code" in df:
            df["product"] = df["stock_code"]
        elif "product" not in df and "description" in df:
            df["product"] = df["description"]
        required_cols = required[kind] + ["product"]
    else:
        required_cols = required[kind]
    missing = sorted(set(required_cols) - set(df))
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    original = len(df)
    duplicates = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()
    for c in ["product", "category", "invoice_no", "country", "description", "status"]:
        if c in df:
            df[c] = df[c].astype("string").str.strip().replace("", pd.NA)
    numeric = {
        "sales": ["units", "price", "unit_cost", "marketing_spend", "expenses"],
        "expenses": ["amount"],
        "inventory": ["price", "unit_cost", "stock"],
    }[kind]
    for c in numeric:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce").replace([np.inf, -np.inf], np.nan)
    if "date" in required_cols:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed", utc=True)
    valid = ~df[required_cols].isna().any(axis=1)
    if kind == "inventory":
        valid &= (df[["stock", "price", "unit_cost"]] >= 0).all(axis=1)
    elif kind == "sales":
        # Keep the sale even if its costs are unknown.
        for c in ["unit_cost", "marketing_spend", "expenses"]:
            if c in df:
                df.loc[df[c] < 0, c] = np.nan
    invalid = int((~valid).sum())
    df = df[valid].copy()
    if df.empty:
        raise ValueError("No usable rows remain after validating required fields.")
    if "date" in df:
        df["month"] = df["date"].dt.strftime("%Y-%m")
    quality = {"input_rows": original, "duplicate_rows_removed": duplicates,
               "invalid_rows_excluded": invalid, "analyzed_rows": len(df)}
    df.attrs["dataset_kind"] = kind
    return df, quality


def _outliers(df, column):
    """Flag values outside the 1.5 IQR range, but keep them for review."""
    values = df[column]
    if len(values) < 4:
        return {"method": "1.5 IQR", "metric": column, "count": 0, "examples": [],
                "note": "At least four observations are needed."}
    q1, q3 = values.quantile([0.25, 0.75])
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    flagged = df[(values < low) | (values > high)]
    cols = [c for c in ["date", "product", "category", column] if c in df]
    return {"method": "1.5 IQR", "metric": column, "lower_bound": _number(low),
            "upper_bound": _number(high), "count": len(flagged),
            "examples": _records(flagged[cols].head(10)),
            "note": "Unusual values are retained. Flags are not proof of errors."}


def _financials(df):
    revenue = float(df["revenue"].sum())
    known = lambda c: c in df and bool(df[c].notna().all())
    cogs = float((df["units"] * df["unit_cost"]).sum()) if known("unit_cost") else None
    marketing = float(df["marketing_spend"].sum()) if known("marketing_spend") else None
    expenses = float(df["expenses"].sum()) if known("expenses") else None
    gross = revenue - cogs if cogs is not None else None
    costs = cogs + marketing + expenses if all(x is not None for x in [cogs, marketing, expenses]) else None
    profit = revenue - costs if costs is not None else None
    return {"revenue": _number(revenue), "units": _number(df["units"].sum()),
            "cogs": _number(cogs), "marketing": _number(marketing), "expenses": _number(expenses),
            "total_costs": _number(costs), "gross_profit": _number(gross), "profit": _number(profit),
            "gross_margin_pct": _pct(gross, revenue) if gross is not None else None,
            "margin_pct": _pct(profit, revenue) if profit is not None else None}


def _sales(df):
    df["revenue"] = df["units"] * df["price"]
    if not np.isfinite(df["revenue"]).all():
        raise ValueError("Revenue calculation exceeds the supported numeric range.")
    cancelled = (df["invoice_no"].str.upper().str.startswith("C", na=False)
                 if "invoice_no" in df else pd.Series(False, index=df.index))
    positive = ~cancelled & (df["units"] > 0) & (df["price"] > 0)
    totals = _financials(df)
    totals.update({"positive_sales_revenue": _number(df.loc[positive, "revenue"].sum()),
                   "negative_transaction_value": _number(-df.loc[df.revenue < 0, "revenue"].sum()),
                   "positive_units_sold": _number(df.loc[positive, "units"].sum()),
                   "orders": int(df["invoice_no"].nunique()) if "invoice_no" in df else None,
                   "products": int(df["product"].nunique())})
    products = []
    for product, group in df.groupby("product", sort=True):
        item = {"product": str(product), **_financials(group)}
        item["gross_margin"] = item["gross_margin_pct"]  # backend contract
        item["share_pct"] = _pct(item["revenue"], totals["revenue"])
        if "description" in group and group.description.notna().any():
            item["description"] = str(group.description.dropna().iloc[-1])
        products.append(item)
    products.sort(key=lambda p: (-p["revenue"], p["product"]))
    trend = [{"period": str(month), **_financials(group)} for month, group in df.groupby("month", sort=True)]
    for i, month in enumerate(trend):
        previous = trend[i - 1] if i else None
        consecutive = previous and pd.Period(month["period"], "M") - 1 == pd.Period(previous["period"], "M")
        month["revenue_change_pct"] = (_pct(month["revenue"] - previous["revenue"], previous["revenue"])
                                       if consecutive else None)
    countries = []
    if "country" in df:
        countries = [{"country": str(c), "revenue": _number(g.revenue.sum())}
                     for c, g in df.groupby("country")]
        countries.sort(key=lambda c: -c["revenue"])
    findings = [f"Net recorded revenue is {totals['revenue']:,.2f} across {len(df):,} transaction rows."]
    if products:
        top = products[0]
        findings.append(f"Highest net revenue product: {top['product']} ({top['revenue']:,.2f}).")
    margins = [p for p in products if p["gross_margin"] is not None and p["revenue"] > 0]
    if margins:
        low = min(margins, key=lambda p: p["gross_margin"])
        findings.append(f"Lowest known product gross margin: {low['product']} ({low['gross_margin']:.2f}%).")
    if len(trend) >= 2:
        first, last = trend[0], trend[-1]
        change = _pct(last["revenue"] - first["revenue"], first["revenue"])
        if change is not None:
            findings.append(f"Recorded revenue changed by {change:+.2f}% between {first['period']} and {last['period']}; coverage may include partial months.")
    anomalies = _outliers(df, "revenue")
    anomalies.update({"cancellation_rows": int(cancelled.sum()), "negative_quantity_rows": int((df.units < 0).sum()),
                      "nonpositive_price_rows": int((df.price <= 0).sum())})
    limitations = ["Revenue is units multiplied by price. Net recorded revenue includes returns and adjustments.",
                   "Stock codes can include postage, fees and manual adjustments; highest revenue does not necessarily identify a physical retail item.",
                   "Transaction rows are not order counts; orders require invoice identifiers.",
                   "No currency conversion is performed. Do not mix currencies in one table.",
                   "Monthly totals cover observed dates; missing months are not assumed to be zero.",
                   "Expense and inventory samples are unrelated sources and must not be joined to retail without verified keys."]
    if totals["cogs"] is None:
        limitations.append("Product costs are missing or incomplete; gross profit and margins are unavailable for the overall dataset.")
    if totals["profit"] is None:
        limitations.append("Net profit requires complete unit_cost, marketing_spend and expenses fields, including explicit zeros where applicable.")
    kpis = [{"label": label, "value": totals[key]} for label, key in [
        ("Total Revenue", "revenue"), ("Total Units Sold", "positive_units_sold"),
        ("Total Costs", "total_costs"), ("Net Profit", "profit"), ("Profit Margin (%)", "margin_pct")]]
    return dict(totals=totals, kpis=kpis, trend=trend, by_product=products, by_country=countries,
                findings=findings, anomalies=anomalies, limitations=limitations)


def _expenses(df):
    total = _number(df.amount.sum())
    categories = [{"category": str(c), "amount": _number(g.amount.sum()), "share_pct": _pct(g.amount.sum(), total)}
                  for c, g in df.groupby("category")]
    categories.sort(key=lambda c: -c["amount"])
    statuses = ([{"status": str(s), "amount": _number(g.amount.sum()), "rows": len(g)}
                 for s, g in df.groupby("status", dropna=False)] if "status" in df else [])
    return dict(totals={"recorded_expenses": total, "expense_rows": len(df)},
                kpis=[{"label": "Recorded Expenses (all statuses)", "value": total}],
                trend=[{"period": str(m), "amount": _number(g.amount.sum())} for m, g in df.groupby("month", sort=True)],
                by_product=[], by_category=categories, by_status=statuses,
                findings=[f"Recorded expense amounts total {total:,.2f} across {len(df)} rows (all statuses).",
                          f"Largest expense category: {categories[0]['category']} ({categories[0]['amount']:,.2f})."],
                anomalies={**_outliers(df, "amount"), "negative_amount_rows": int((df.amount < 0).sum())},
                limitations=["Expense requests of every status are included, including pending or rejected entries; recorded total is not cash paid.",
                             "Negative amounts are retained as adjustments; verify their meaning.",
                             "Currency is unspecified unless supplied explicitly. This sample cannot establish retail profit."])


def _inventory(df):
    df["inventory_cost_value"] = df.stock * df.unit_cost
    df["inventory_retail_value"] = df.stock * df.price
    df["unit_margin"] = df.price - df.unit_cost
    df["gross_margin"] = (df.unit_margin / df.price.replace(0, np.nan) * 100).round(2)
    key = "product_id" if "product_id" in df else "product"
    products = []
    for _, row in df.iterrows():
        products.append({"product": str(row[key]), "description": str(row["product"]),
                         "stock": _number(row.stock), "price": _number(row.price),
                         "unit_cost": _number(row.unit_cost), "gross_margin": _number(row.gross_margin),
                         "inventory_cost_value": _number(row.inventory_cost_value),
                         "inventory_retail_value": _number(row.inventory_retail_value)})
    totals = {"stock_units": _number(df.stock.sum()), "product_rows": len(df),
              "inventory_cost_value": _number(df.inventory_cost_value.sum()),
              "inventory_retail_value": _number(df.inventory_retail_value.sum()),
              "out_of_stock_products": int((df.stock == 0).sum())}
    return dict(totals=totals, kpis=[{"label": k.replace("_", " ").title(), "value": v} for k, v in totals.items()],
                trend=[], by_product=products,
                findings=[f"Inventory contains {totals['stock_units']:,.2f} units across {len(df)} product records.",
                          f"{totals['out_of_stock_products']} product records have no stock.",
                          f"Inventory cost value is {totals['inventory_cost_value']:,.2f}; potential retail value is {totals['inventory_retail_value']:,.2f}."],
                anomalies={**_outliers(df, "stock"), "negative_margin_products": int((df.unit_margin < 0).sum()),
                           "duplicate_product_ids": int(df[key].duplicated().sum())},
                limitations=["Inventory values and listed-price margins are potential values, not realized sales or profit.",
                             "No low-stock threshold is assumed. Out of stock means exactly zero units.",
                             "Currency is unspecified unless supplied explicitly. No relationship with the UCI retail products is established."])


def analyze_business_data(data, dataset_id="", kind="auto", currency=None):
    """Return totals, product results and findings that can be sent as JSON."""
    df, quality = prepare_dataframe(data, kind)
    kind = df.attrs["dataset_kind"]
    retail = "invoice_no" in df and "stock_code" in df
    result = {"dataset_id": dataset_id, "dataset_kind": kind, "currency": currency or ("GBP" if retail else None),
              "source": "calculated", "quality": quality,
              "date_range": ({"start": df.date.min().date().isoformat(), "end": df.date.max().date().isoformat()}
                             if "date" in df else None)}
    result.update({"sales": _sales, "expenses": _expenses, "inventory": _inventory}[kind](df))
    return result
