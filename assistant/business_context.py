
from data_loader import load_data
import pandas as pd


def get_business_context():
    df = load_data()

    df = df[
        (~df["Invoice"].astype(str).str.startswith("C")) &
        (df["Quantity"] > 0) &
        (df["Price"] > 0)
    ].copy()

    df["Revenue"] = df["Quantity"] * df["Price"]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    total_revenue = df["Revenue"].sum()
    total_orders = df["Invoice"].nunique()
    total_products = df["StockCode"].nunique()

    top_products = (
        df.groupby("Description")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    top_countries = (
        df.groupby("Country")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    top_products_by_quantity = (
        df.groupby("Description")["Quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    monthly_sales = (
        df.groupby(df["InvoiceDate"].dt.to_period("M"))["Revenue"]
        .sum()
        .sort_index()
    )

    context = f"""
Business Dataset: Online Retail II (2009-2010)

Total Revenue: £{total_revenue:,.2f}
Total Orders: {total_orders:,}
Total Unique Products: {total_products:,}

Top 10 Products by Revenue:
{top_products.to_string()}

Top 10 Countries by Revenue:
{top_countries.to_string()}

Top 10 Products by Units Sold:
{top_products_by_quantity.to_string()}

Monthly Revenue:
{monthly_sales.to_string()}

Important Information:
- Revenue is calculated as Quantity * Price.
- Cancelled invoices and transactions with non-positive quantities or prices are excluded.
- Profit and operating expenses cannot be calculated from this dataset.
- The data covers only the first Excel sheet (2009-2010).
- Some entries, such as Manual and POSTAGE, may not represent actual retail products.
- Only the summaries above are available to the assistant.
"""
    return context
