"""Retail Intelligence — portfolio business analytics dashboard with synthetic data."""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from analytics_core import load_sales, filter_sales, sales_kpis, data_quality

DB = Path(__file__).with_name("retail_analytics.db")
st.set_page_config(page_title="Retail Intelligence | SQL Analytics", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root { --brand: #3b82f6; --ink: #0f172a; --muted: #64748b; }
.block-container { max-width: 1440px; padding-top: 1.7rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: #0f172a; border-right: 1px solid #26344b; }
[data-testid="stSidebar"] * { color: #e2e8f0; }
[data-testid="stSidebar"] [data-baseweb="tag"] { background-color: #334155; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { font-weight: 600; }
[data-testid="stMetric"] {
  background: rgba(100,116,139,.08); border: 1px solid rgba(100,116,139,.22);
  border-radius: 16px; padding: 18px 20px; min-height: 110px;
}
[data-testid="stMetricLabel"] { font-weight: 600; }
[data-testid="stMetricValue"] { font-size: clamp(1.4rem, 2.4vw, 2rem); letter-spacing: -.035em; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px; }
h1, h2, h3 { letter-spacing: -.035em; }
h1 { font-weight: 800; }
h3 { margin-top: 1.25rem; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
[data-testid="stDownloadButton"] button { border-radius: 10px; font-weight: 600; }
.hero {
  padding: 24px 28px; border-radius: 18px; margin: 0 0 14px;
  background: linear-gradient(115deg,#0f172a 0%,#1d3558 65%,#1d4ed8 150%);
  color: #f8fafc; border: 1px solid #334155;
}
.hero .eyebrow { color: #93c5fd; font-size: .76rem; font-weight: 700; letter-spacing: .14em; }
.hero h1 { color: #fff; margin: 8px 0; font-size: clamp(1.8rem,3vw,2.7rem); }
.hero p { color: #cbd5e1; margin: 0; }
.section-kicker { font-size: .76rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; color: #64748b; }
@media (max-width: 700px) { .hero { padding: 18px; } .block-container { padding-top: 1rem; } }
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
    return load_sales(DB)

data = load_lines()
if data.empty:
    st.warning("No completed sales found.")
    st.stop()

with st.sidebar:
    st.markdown("## ◈ Retail Intelligence")
    st.caption("ANALYTICS WORKSPACE  /  V2.0")
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
filtered = filter_sales(data, start, end, categories, regions, segments)

st.markdown(
    '<div class="hero"><div class="eyebrow">BUSINESS INTELLIGENCE / PORTFOLIO PROJECT</div>'
    '<h1>Retail Intelligence</h1>'
    '<p>Explore sales performance, product trends, and customer behavior through SQL-powered analytics.</p>'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown(f"**{page}** &nbsp; · &nbsp; :blue[**SYNTHETIC DATA**] &nbsp; · &nbsp; {start:%b %d, %Y} – {end:%b %d, %Y} &nbsp; · &nbsp; {len(filtered):,} sales lines")
st.divider()
if filtered.empty:
    st.warning("No sales match your filters. Adjust the date range or selections.")
    st.stop()

kpis = sales_kpis(filtered)
revenue, orders, customers, aov = (kpis[key] for key in ("revenue", "orders", "customers", "aov"))
period_days = (end - start).days + 1
prev_end = start - pd.Timedelta(days=1)
prev_start = start - pd.Timedelta(days=period_days)
previous = filter_sales(data, prev_start, prev_end, categories, regions, segments)
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
    st.markdown("#### Additional performance indicators")
    e, f, g = st.columns(3)
    e.metric("Units sold", f"{kpis['units']:,}")
    f.metric("Revenue per customer", f"${kpis['revenue_per_customer']:,.2f}" if customers else "—")
    g.metric("Top category share", f"{kpis['top_category_share']:.1%}" if revenue else "—")

monthly = filtered.assign(month=filtered["order_date"].dt.to_period("M").dt.to_timestamp()).groupby("month")["revenue"].sum()
by_category = filtered.groupby("category")["revenue"].sum().sort_values(ascending=False)
by_region = filtered.groupby("region")["revenue"].sum().sort_values(ascending=False)
by_product = filtered.groupby("product_name")["revenue"].sum().sort_values(ascending=False)

if page == "Executive Overview":
    metrics()
    if not prev_revenue:
        st.caption("Growth deltas unavailable: no comparable sales in the preceding period.")
    st.markdown("### Revenue trends & product mix")
    st.caption("Monthly sales trend and contribution by product category")
    left, right = st.columns([1.5, 1])
    with left:
        st.line_chart(monthly, x_label="Month", y_label="Revenue ($)")
    with right:
        st.bar_chart(by_category, x_label="Category", y_label="Revenue ($)")
    st.markdown("### Daily revenue and 7-day moving average")
    st.caption("A trailing moving average smooths daily fluctuations; zero-sales dates are included.")
    daily = filtered.groupby(filtered["order_date"].dt.normalize())["revenue"].sum()
    daily = daily.reindex(pd.date_range(start, end, freq="D"), fill_value=0)
    daily_trends = pd.DataFrame({
        "Daily revenue": daily,
        "7-day moving average": daily.rolling(7, min_periods=1).mean(),
    })
    st.line_chart(daily_trends, x_label="Date", y_label="Revenue ($)")
    st.markdown("### Executive highlights")
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
    st.caption("Compare revenue across regions and product categories")
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
    repeat_customers = kpis["repeat_customers"]
    a.metric("Active customers", f"{customers:,}")
    b.metric("Repeat customers", f"{repeat_customers:,}")
    c.metric("Repeat customer share", f"{kpis['repeat_share']:.1%}" if customers else "—")
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
    quality = data_quality(filtered)
    missing = quality["missing_required"]
    negative = quality["negative_revenue"]
    a.metric("Missing key values", missing)
    b.metric("Negative revenue lines", negative)
    c.metric("Filtered order lines", f"{len(filtered):,}")
    st.markdown("### Exportable transaction detail")
    st.dataframe(filtered.sort_values("order_date", ascending=False), use_container_width=True, hide_index=True)
    st.download_button("⬇ Download filtered sales CSV", filtered.to_csv(index=False).encode("utf-8"), file_name="retail_intelligence_filtered.csv", mime="text/csv")
    st.caption("Quality checks cover the filtered completed-order lines; they are not a full database audit.")

st.divider()
st.caption("RETAIL INTELLIGENCE  ·  Built with Python, SQL, SQLite, Pandas & Streamlit  ·  Synthetic demonstration data  ·  Portfolio project")
