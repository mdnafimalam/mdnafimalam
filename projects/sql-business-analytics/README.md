# SQL Business Analytics Dashboard

A reproducible retail sales analytics portfolio project using **SQLite, Python, Pandas, and Streamlit**.

> **Data disclosure:** This project uses synthetic, deterministic demonstration data, not real company or customer records. Business findings are illustrative.

## Features
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

Open the Streamlit URL printed by `streamlit run app.py`. Select a date range and categories to explore trends and download filtered data. The dashboard is local by default; this repository publishes the code, **not a hosted dashboard**.

## Limitations and next steps

- Synthetic sales data; no causal or production business conclusions
- No refunds, discounts, taxes, shipping, or inventory costs modeled
- Future enhancements: customer cohorts, gross margin, deployment, automated tests

**Author:** Md. Nafim Alam — Management Information Systems, Emporia State University.
