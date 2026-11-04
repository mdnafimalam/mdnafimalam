"""Interactive Streamlit dashboard for synthetic retail sales."""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

DB = Path(__file__).with_name("retail_analytics.db")

st.set_page_config(page_title="Retail Sales | SQL Analytics", page_icon="📊", layout="wide")
st.title("📊 Retail Sales Analytics")
st.caption("Portfolio demonstration · Synthetic retail data · Completed orders only")

if not DB.exists():
    # Streamlit Community Cloud starts with a fresh filesystem.
    # Generate deterministic demo data once when the database is absent.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from generate_data import main as generate_demo_data
        generate_demo_data()
    except (OSError, sqlite3.Error, ImportError) as exc:
        st.error(f"Could not initialize the demonstration database: {exc}")
        st.stop()


@st.cache_data
def load_lines():
    with sqlite3.connect(DB) as con:
        df = pd.read_sql_query(
            """
            SELECT o.order_id, o.order_date, o.customer_id, c.segment, c.region,
                   p.product_name, p.category, oi.quantity, oi.unit_price,
                   ROUND(oi.quantity * oi.unit_price, 2) AS revenue
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            JOIN order_items oi ON oi.order_id = o.order_id
            JOIN products p ON p.product_id = oi.product_id
            WHERE o.status = 'Completed'
            """,
            con,
        )
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


data = load_lines()
if data.empty:
    st.warning("No completed sales found.")
    st.stop()

with st.sidebar:
    st.header("Filters")
    earliest = data["order_date"].min().date()
    latest = data["order_date"].max().date()
    dates = st.date_input("Order date range", (earliest, latest), min_value=earliest, max_value=latest)
    categories = st.multiselect(
        "Product categories",
        sorted(data["category"].unique()),
        default=sorted(data["category"].unique()),
    )

if not isinstance(dates, (tuple, list)) or len(dates) != 2:
    st.info("Choose a start and end date.")
    st.stop()

start, end = dates
filtered = data.loc[
    data["order_date"].dt.date.between(start, end)
    & data["category"].isin(categories)
].copy()

if filtered.empty:
    st.warning("No matching sales. Adjust the filters.")
    st.stop()

revenue = filtered["revenue"].sum()
orders = filtered["order_id"].nunique()
customers = filtered["customer_id"].nunique()
aov = revenue / orders if orders else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"${revenue:,.2f}")
c2.metric("Orders", f"{orders:,}")
c3.metric("Average order value*", f"${aov:,.2f}")
c4.metric("Unique customers", f"{customers:,}")
st.caption("*For filtered categories, average order value reflects only selected category revenue per matching order.")

monthly = (
    filtered.assign(month=filtered["order_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("month", as_index=False)["revenue"].sum()
    .set_index("month")
)
by_category = filtered.groupby("category")["revenue"].sum().sort_values(ascending=False)
top_products = filtered.groupby("product_name")["revenue"].sum().nlargest(10)

left, right = st.columns(2)
with left:
    st.subheader("Monthly revenue")
    st.line_chart(monthly)
    st.subheader("Top 10 products")
    st.bar_chart(top_products)
with right:
    st.subheader("Revenue by category")
    st.bar_chart(by_category)
    st.subheader("Revenue by region")
    st.bar_chart(filtered.groupby("region")["revenue"].sum().sort_values(ascending=False))

st.subheader("Filtered sales data")
st.dataframe(filtered.sort_values("order_date", ascending=False), use_container_width=True)
st.download_button(
    "Download filtered CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_sales.csv",
    mime="text/csv",
)
