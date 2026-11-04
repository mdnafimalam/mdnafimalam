"""Reusable, testable analytics functions for Retail Intelligence."""
import sqlite3
from pathlib import Path

import pandas as pd

SALES_SQL = """
SELECT o.order_id, o.order_date, o.customer_id, c.segment, c.region,
       p.product_name, p.category, oi.quantity, oi.unit_price,
       ROUND(oi.quantity * oi.unit_price, 2) AS revenue
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status = 'Completed'
"""

def load_sales(db_path: str | Path) -> pd.DataFrame:
    """Load completed order lines only; each order can have multiple lines."""
    with sqlite3.connect(db_path) as con:
        frame = pd.read_sql_query(SALES_SQL, con)
    frame["order_date"] = pd.to_datetime(frame["order_date"])
    return frame

def filter_sales(frame: pd.DataFrame, start, end, categories, regions, segments) -> pd.DataFrame:
    """Inclusive date range plus AND-combined category, region, segment filters."""
    if start > end:
        raise ValueError("Start date must not be after end date")
    mask = (
        frame["order_date"].dt.date.between(start, end)
        & frame["category"].isin(categories)
        & frame["region"].isin(regions)
        & frame["segment"].isin(segments)
    )
    return frame.loc[mask].copy()

def sales_kpis(frame: pd.DataFrame) -> dict:
    """Distinct orders/customers avoid overcounting multi-line orders."""
    revenue = float(frame["revenue"].sum())
    orders = int(frame["order_id"].nunique())
    customers = int(frame["customer_id"].nunique())
    units = int(frame["quantity"].sum())
    order_counts = frame.groupby("customer_id")["order_id"].nunique()
    repeat_customers = int((order_counts > 1).sum())
    category_revenue = frame.groupby("category")["revenue"].sum()
    return {
        "revenue": revenue,
        "orders": orders,
        "customers": customers,
        "units": units,
        "aov": revenue / orders if orders else 0.0,
        "revenue_per_customer": revenue / customers if customers else 0.0,
        "repeat_customers": repeat_customers,
        "repeat_share": repeat_customers / customers if customers else 0.0,
        "top_category_share": float(category_revenue.max() / revenue) if revenue else 0.0,
    }

def data_quality(frame: pd.DataFrame) -> dict:
    """Checks on the completed-order lines returned by load_sales."""
    required = ["order_id", "order_date", "customer_id", "product_name",
                "category", "segment", "region", "quantity", "unit_price", "revenue"]
    return {
        "missing_required": int(frame[required].isna().sum().sum()),
        "invalid_quantity": int((frame["quantity"] <= 0).sum()),
        "negative_price": int((frame["unit_price"] < 0).sum()),
        "negative_revenue": int((frame["revenue"] < 0).sum()),
        "revenue_mismatches": int(
            ((frame["quantity"] * frame["unit_price"]).round(2) - frame["revenue"]).abs().gt(0.011).sum()
        ),
    }

def database_integrity(db_path: str | Path) -> dict:
    """Check foreign keys, orphan records, and valid order status."""
    with sqlite3.connect(db_path) as con:
        fk_violations = len(con.execute("PRAGMA foreign_key_check").fetchall())
        bad_status = con.execute(
            "SELECT COUNT(*) FROM orders WHERE status NOT IN ('Completed', 'Canceled') OR status IS NULL"
        ).fetchone()[0]
        missing_items = con.execute(
            "SELECT COUNT(*) FROM orders o WHERE NOT EXISTS "
            "(SELECT 1 FROM order_items i WHERE i.order_id = o.order_id)"
        ).fetchone()[0]
    return {
        "foreign_key_violations": fk_violations,
        "invalid_order_status": bad_status,
        "orders_without_items": missing_items,
    }
