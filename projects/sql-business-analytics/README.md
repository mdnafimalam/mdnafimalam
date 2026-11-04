# SQL Business Analytics Dashboard

A reproducible retail sales analytics portfolio project using **SQLite, Python, Pandas, and Streamlit**.

> **Data disclosure:** This project uses synthetic, deterministic demonstration data, not real company or customer records. Business findings are illustrative.

**Live app:** [Open the Streamlit dashboard](https://nafim-sql-analytics.streamlit.app/)\n\n## Features
- SQLite relational database with customers, products, orders, and order items
- Repeatable data generation with a fixed random seed
- SQL analytics: monthly revenue, category performance, top products, repeat customers
- Interactive Streamlit dashboard with date and category filters
- Revenue, orders, average order value, and unique customers KPIs
- CSV download of filtered order-line data

## Quick start

```bash
git clone https://github.com/mdnafimalam/mdnafimalam.git
cd mdnafimalam/projects/sql-business-analytics
python -m pip install -r requirements.txt
python generate_data.py
streamlit run app.py
```

Python 3.10+ recommended. The generated database is local and excluded from version control.

## Project structure

```text
projects/sql-business-analytics/
├── README.md
├── requirements.txt
├── .gitignore
├── generate_data.py
├── analytics.sql
└── app.py
```

## Data model

- `customers(customer_id, segment, region)`
- `products(product_id, product_name, category, unit_price)`
- `orders(order_id, customer_id, order_date, status)`
- `order_items(order_item_id, order_id, product_id, quantity, unit_price)`

**Revenue definition:** sum of `quantity * unit_price` for `Completed` orders only. Prices are snapshotted on order items. Canceled orders are excluded. All displayed dates are based on synthetic order dates.

## SQL skills demonstrated

`JOIN`, `GROUP BY`, `HAVING`, `COUNT(DISTINCT ...)`, `SUM`, `ROUND`, `strftime`, CTEs, and aggregation.

Run saved SQL queries after generating data:

```bash
sqlite3 retail_analytics.db < analytics.sql
```

## Dashboard

Open the Streamlit URL printed by `streamlit run app.py`. Select a date range and categories to explore trends and download filtered data. The dashboard can run locally and has a Streamlit Community Cloud deployment. The deployed app generates its demo database on startup if missing.

## Limitations and next steps

- Synthetic sales data; no causal or production business conclusions
- No refunds, discounts, taxes, shipping, or inventory costs modeled
- Future enhancements: customer cohorts, gross margin, deployment, automated tests

**Author:** Md. Nafim Alam — Management Information Systems, Emporia State University.


## Advanced dashboard features

- Period-over-period revenue and order comparisons for the selected date range (when prior-period data exists).
- Revenue by customer segment and top-five products by revenue.
- Automatically generated descriptive business insights for leading category, region, and product.
- Data-quality checks for missing key values, negative revenue lines, and filtered order-line counts.
- Interactive category and date filters, SQL-backed KPIs, regional and monthly charts, and CSV export.

**Important:** The dataset is generated, deterministic synthetic retail data. Metrics and recommendations are demonstration outputs, not real-world business results. For date windows without preceding-period data, growth percentages are intentionally omitted.


## Retail Intelligence redesign

The Streamlit application now includes four sidebar-navigated views: **Executive Overview**, **Sales Performance**, **Customer Insights**, and **Reports & Data Quality**. Global date, category, region, and customer-segment filters apply across the views. The interface includes period-over-period KPI comparisons where preceding-period data exists, product performance tables, repeat-customer metrics, and downloadable filtered CSV reports.

The styling is designed for a professional portfolio presentation. All data remains deterministic and synthetic. The hosted deployment may take a short time to rebuild after a GitHub commit.


## Advanced KPI and chart enhancements

- **New KPIs:** units sold, revenue per customer, and the share of revenue contributed by the leading product category.
- **Revenue trend:** daily sales alongside a trailing seven-day moving average; dates without sales are displayed as zero revenue.
- **Regional product mix:** category-by-region revenue matrix for side-by-side comparison.
- **Customer segment performance:** segment-level revenue, distinct orders, customers, units, average order value, and revenue per customer.

All views respect the dashboard's date, category, region, and customer-segment filters. These are descriptive metrics on synthetic demo data; period comparisons require available prior-period records.

## Automated tests and continuous integration

The dashboard's calculations are implemented in `analytics_core.py`, shared by the Streamlit app and automated tests. `test_analytics.py` includes **13 unit and SQLite integration tests** covering:

- Revenue, distinct orders, average order value, units sold, and category share
- Unique customers, repeat customers, repeat share, and revenue per customer
- Inclusive date filters and combined category/region/segment filters
- Empty selections and invalid date ranges
- Missing data, invalid quantities, negative values, and line-total mismatches
- Generated database tables, completed-only sales, SQL/Python revenue agreement, and referential integrity

Run tests locally (from `projects/sql-business-analytics`):

```bash
py -m pip install -r requirements.txt
py -m unittest discover -v -p "test_*.py"
```

On macOS/Linux, use `python3` instead of `py`. The tests create their own temporary SQLite database and do **not** overwrite your dashboard's local database.

GitHub Actions runs the test suite automatically on pushes and pull requests affecting this project; see `.github/workflows/sql-dashboard-tests.yml`. A passing workflow should be confirmed in the repository's **Actions** tab before claiming CI is green.
