"""Retail Intelligence — portfolio business analytics dashboard with synthetic data."""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

DB = Path(__file__).with_name("retail_analytics.db")
st.set_page_config(page_title="Retail Intelligence | SQL Analytics", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.block-container {max-width: 1450px; padding-top: 1.8rem; padding-bottom: 3rem;}
[data-testid="stSidebar"] {background: #111c2e;}
[data-testid="stSidebar"] * {color: #e8eef8;}
[data-testid="stMetric"] {background: rgba(120,140,170,.10); border: 1px solid rgba(140,155,180,.20); border-radius: 14px; padding: 18px 20px;}
[data-testid="stMetricLabel"] {font-weight: 600;}
h1, h2, h3 {letter-spacing: -.025em;}
div[data-testid="stDataFrame"] {border-radius: 12px; overflow: hidden;}
</style>
""", unsafe_allow_html=True)

if not DB.exists():
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
        df = pd.read_sql_query("""
            SELECT o.order_id, o.order_date, o.customer_id, c.segment, c.region,
                   p.product_name, p.category, oi.quantity, oi.unit_price,
                   ROUND(oi.quantity * oi.unit_price, 2) AS revenue
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            JOIN order_items oi ON oi.order_id = o.order_id
            JOIN products p ON p.product_id = oi.product_id
            WHERE o.status = 'Completed'
        """, con)
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df

data = load_lines()
if data.empty:
    st.warning("No completed sales found.")
    st.stop()

with st.sidebar:
    st.markdown("## 📈 Retail Intelligence")
    st.caption("BUSINESS ANALYTICS · PORTFOLIO")
    st.divider()
    page = st.radio("Workspace", ["Executive Overview", "Sales Performance", "Customer Insights", "Reports & Data Quality"], label_visibility="collapsed")
    st.divider()
    st.markdown("#### Global filters")
    earliest, latest = data["order_date"].min().date(), data["order_date"].max().date()
    dates = st.date_input("Order date range", (earliest, latest), min_value=earliest, max_value=latest)
    categories = st.multiselect("Category", sorted(data["category"].unique()), default=sorted(data["category"].unique()))
    regions = st.multiselect("Region", sorted(data["region"].unique()), default=sorted(data["region"].unique()))
    segments = st.multiselect("Customer segment", sorted(data["segment"].unique()), default=sorted(data["segment"].unique()))
    st.divider()
    st.caption("🔬 Synthetic retail data · Not actual business transactions")

if not isinstance(dates, (tuple, list)) or len(dates) != 2:
    st.info("Choose both a start and an end date.")
    st.stop()
start, end = dates
filtered = data.loc[
    data["order_date"].dt.date.between(start, end)
    & data["category"].isin(categories)
    & data["region"].isin(regions)
    & data["segment"].isin(segments)
].copy()

st.title("Retail Intelligence")
st.caption("Interactive SQL-powered business analytics  ·  Synthetic portfolio dataset")
st.markdown(f"**{page}** &nbsp; · &nbsp; {start:%b %d, %Y} — {end:%b %d, %Y} &nbsp; · &nbsp; {len(filtered):,} order lines")
st.divider()
if filtered.empty:
    st.warning("No sales match your filters. Adjust the date range or selections.")
    st.stop()

revenue = filtered["revenue"].sum()
orders = filtered["order_id"].nunique()
customers = filtered["customer_id"].nunique()
aov = revenue / orders if orders else 0
period_days = (end - start).days + 1
prev_end = start - pd.Timedelta(days=1)
prev_start = start - pd.Timedelta(days=period_days)
previous = data.loc[
    data["order_date"].dt.date.between(prev_start, prev_end)
    & data["category"].isin(categories)
    & data["region"].isin(regions)
    & data["segment"].isin(segments)
]
prev_revenue = previous["revenue"].sum()
prev_orders = previous["order_id"].nunique()
revenue_delta = f"{(revenue / prev_revenue - 1) * 100:+.1f}%" if prev_revenue else None
orders_delta = f"{(orders / prev_orders - 1) * 100:+.1f}%" if prev_orders else None

def metrics():
    a, b, c, d = st.columns(4)
    a.metric("Total revenue", f"$" + f"{revenue:,.2f}", delta=revenue_delta)
    b.metric("Completed orders", f"{orders:,}", delta=orders_delta)
    c.metric("Average order value", f"$" + f"{aov:,.2f}")
    d.metric("Unique customers", f"{customers:,}")
    e, f, g = st.columns(3)
    e.metric("Units sold", f"{int(filtered['quantity'].sum()):,}")
    f.metric("Revenue per customer", f"${revenue / customers:,.2f}" if customers else "—")
    g.metric("Top category share", f"{by_category.iloc[0] / revenue:.1%}" if revenue else "—")

monthly = filtered.assign(month=filtered["order_date"].dt.to_period("M").dt.to_timestamp()).groupby("month")["revenue"].sum()
by_category = filtered.groupby("category")["revenue"].sum().sort_values(ascending=False)
by_region = filtered.groupby("region")["revenue"].sum().sort_values(ascending=False)
by_product = filtered.groupby("product_name")["revenue"].sum().sort_values(ascending=False)

if page == "Executive Overview":
    metrics()
    if not prev_revenue:
        st.caption("Growth deltas unavailable: no comparable sales in the preceding period.")
    st.markdown("### Revenue trends & product mix")
    left, right = st.columns([1.5, 1])
    with left:
        st.line_chart(monthly, x_label="Month", y_label="Revenue ($)")
    with right:
        st.bar_chart(by_category, x_label="Category", y_label="Revenue ($)")
    st.markdown("### Daily revenue and 7-day moving average")
    daily = filtered.groupby(filtered["order_date"].dt.normalize())["revenue"].sum()
    daily = daily.reindex(pd.date_range(start, end, freq="D"), fill_value=0)
    daily_trends = pd.DataFrame({
        "Daily revenue": daily,
        "7-day moving average": daily.rolling(7, min_periods=1).mean(),
    })
    st.line_chart(daily_trends, x_label="Date", y_label="Revenue ($)")
    st.markdown("### Business highlights")
    x, y, z = st.columns(3)
    x.info(f"**Leading category**\n\n{by_category.index[0]}")
    y.info(f"**Top region**\n\n{by_region.index[0]}")
    z.info(f"**Top product by revenue**\n\n{by_product.index[0]}")
    st.caption("Descriptive findings only; synthetic data cannot support real-world business recommendations.")

elif page == "Sales Performance":
    metrics()
    st.markdown("### Revenue by region and product")
    left, right = st.columns(2)
    with left:
        st.bar_chart(by_region, x_label="Region", y_label="Revenue ($)")
    with right:
        st.bar_chart(by_product.head(10), x_label="Product", y_label="Revenue ($)")
    st.markdown("### Category performance by region")
    category_region = filtered.pivot_table(
        index="region", columns="category", values="revenue", aggfunc="sum", fill_value=0
    )
    st.dataframe(
        category_region.style.format("${:,.2f}"),
        use_container_width=True,
    )
    st.markdown("### Product performance table")
    product_table = filtered.groupby(["category", "product_name"]).agg(
        revenue=("revenue", "sum"), units_sold=("quantity", "sum"), order_count=("order_id", "nunique")
    ).reset_index().sort_values("revenue", ascending=False)
    st.dataframe(product_table, use_container_width=True, hide_index=True)

elif page == "Customer Insights":
    st.markdown("### Customer behavior")
    a, b, c = st.columns(3)
    orders_per_customer = filtered.groupby("customer_id")["order_id"].nunique()
    repeat_customers = int((orders_per_customer > 1).sum())
    a.metric("Active customers", f"{customers:,}")
    b.metric("Repeat customers", f"{repeat_customers:,}")
    c.metric("Repeat customer share", f"{repeat_customers / customers:.1%}" if customers else "—")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Revenue by customer segment")
        st.bar_chart(filtered.groupby("segment")["revenue"].sum().sort_values(ascending=False))
    with right:
        st.markdown("#### Customers by region")
        st.bar_chart(filtered.groupby("region")["customer_id"].nunique().sort_values(ascending=False))
    st.markdown("### Segment performance")
    segment_summary = filtered.groupby("segment").agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
        units=("quantity", "sum"),
    )
    segment_summary["average_order_value"] = segment_summary["revenue"] / segment_summary["orders"]
    segment_summary["revenue_per_customer"] = segment_summary["revenue"] / segment_summary["customers"]
    st.dataframe(
        segment_summary.reset_index(),
        hide_index=True,
        use_container_width=True,
        column_config={
            "revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
            "average_order_value": st.column_config.NumberColumn("Avg. order value", format="$%.2f"),
            "revenue_per_customer": st.column_config.NumberColumn("Revenue / customer", format="$%.2f"),
        },
    )
    st.caption("Repeat customer = customer with more than one completed order in the selected filters.")

else:
    st.markdown("### Data quality")
    a, b, c = st.columns(3)
    missing = int(filtered[["order_id", "customer_id", "product_name", "revenue"]].isna().sum().sum())
    negative = int((filtered["revenue"] < 0).sum())
    a.metric("Missing key values", missing)
    b.metric("Negative revenue lines", negative)
    c.metric("Filtered order lines", f"{len(filtered):,}")
    st.markdown("### Exportable transaction detail")
    st.dataframe(filtered.sort_values("order_date", ascending=False), use_container_width=True, hide_index=True)
    st.download_button("⬇ Download filtered sales CSV", filtered.to_csv(index=False).encode("utf-8"), file_name="retail_intelligence_filtered.csv", mime="text/csv")
    st.caption("Quality checks cover the filtered completed-order lines; they are not a full database audit.")

st.divider()
st.caption("Built with Python · SQL · SQLite · Pandas · Streamlit | Portfolio demonstration using deterministic synthetic data.")
