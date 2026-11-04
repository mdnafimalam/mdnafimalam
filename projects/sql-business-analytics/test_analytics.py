"""Unit and integration tests for the dashboard's production analytics functions."""
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import generate_data
from analytics_core import (
    data_quality, database_integrity, filter_sales, load_sales, sales_kpis,
)

class AnalyticsUnitTests(unittest.TestCase):
    def setUp(self):
        self.sales = pd.DataFrame([
            # Order 1 has TWO lines; it must count as one order.
            (1, "2026-01-01", 10, "Consumer", "West", "Mouse", "Electronics", 2, 10.0, 20.0),
            (1, "2026-01-01", 10, "Consumer", "West", "Pen", "Office", 1, 5.0, 5.0),
            (2, "2026-01-02", 10, "Consumer", "West", "Mouse", "Electronics", 1, 10.0, 10.0),
            (3, "2026-01-03", 20, "Student", "Midwest", "Pen", "Office", 3, 5.0, 15.0),
        ], columns=["order_id", "order_date", "customer_id", "segment", "region",
                    "product_name", "category", "quantity", "unit_price", "revenue"])
        self.sales["order_date"] = pd.to_datetime(self.sales["order_date"])

    def test_revenue_and_order_kpis(self):
        k = sales_kpis(self.sales)
        self.assertAlmostEqual(k["revenue"], 50.0)
        self.assertEqual(k["orders"], 3)
        self.assertAlmostEqual(k["aov"], 50 / 3)
        self.assertEqual(k["units"], 7)
        self.assertAlmostEqual(k["top_category_share"], 0.6)

    def test_customer_kpis(self):
        k = sales_kpis(self.sales)
        self.assertEqual(k["customers"], 2)
        self.assertEqual(k["repeat_customers"], 1)
        self.assertAlmostEqual(k["repeat_share"], 0.5)
        self.assertAlmostEqual(k["revenue_per_customer"], 25.0)

    def test_empty_kpis_have_no_division_by_zero(self):
        k = sales_kpis(self.sales.iloc[0:0])
        self.assertEqual(k["orders"], 0)
        self.assertEqual(k["aov"], 0)
        self.assertEqual(k["repeat_share"], 0)
        self.assertEqual(k["top_category_share"], 0)

    def test_inclusive_date_filter(self):
        result = filter_sales(self.sales, date(2026, 1, 2), date(2026, 1, 3),
                              ["Office", "Electronics"], ["West", "Midwest"], ["Consumer", "Student"])
        self.assertEqual(set(result["order_id"]), {2, 3})

    def test_category_region_segment_filters(self):
        result = filter_sales(self.sales, date(2026, 1, 1), date(2026, 1, 3),
                              ["Electronics"], ["West"], ["Consumer"])
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(sales_kpis(result)["revenue"], 30.0)

    def test_empty_filter_selection(self):
        result = filter_sales(self.sales, date(2026, 1, 1), date(2026, 1, 3),
                              [], ["West"], ["Consumer"])
        self.assertTrue(result.empty)

    def test_invalid_date_range(self):
        with self.assertRaises(ValueError):
            filter_sales(self.sales, date(2026, 1, 3), date(2026, 1, 1),
                         ["Office"], ["West"], ["Consumer"])

    def test_data_quality_detects_invalid_lines(self):
        broken = self.sales.copy()
        broken.loc[0, "quantity"] = 0
        broken.loc[1, "revenue"] = -5
        broken.loc[2, "product_name"] = None
        q = data_quality(broken)
        self.assertEqual(q["invalid_quantity"], 1)
        self.assertEqual(q["negative_revenue"], 1)
        self.assertEqual(q["missing_required"], 1)
        self.assertGreater(q["revenue_mismatches"], 0)

    def test_clean_fixture_has_no_quality_issues(self):
        self.assertTrue(all(v == 0 for v in data_quality(self.sales).values()))

class GeneratedDatabaseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.tmp.name) / "test_retail.db"
        with patch.object(generate_data, "DB", cls.db):
            generate_data.main()
        cls.sales = load_sales(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_generated_database_has_expected_tables_and_rows(self):
        with sqlite3.connect(self.db) as con:
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            order_count = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        self.assertTrue({"customers", "products", "orders", "order_items"}.issubset(tables))
        self.assertEqual(order_count, 1500)
        self.assertFalse(self.sales.empty)

    def test_canceled_orders_are_excluded(self):
        with sqlite3.connect(self.db) as con:
            completed = con.execute("SELECT COUNT(*) FROM orders WHERE status='Completed'").fetchone()[0]
            canceled = con.execute("SELECT COUNT(*) FROM orders WHERE status='Canceled'").fetchone()[0]
        self.assertGreater(canceled, 0)
        self.assertEqual(sales_kpis(self.sales)["orders"], completed)

    def test_revenue_matches_independent_sql_aggregate(self):
        with sqlite3.connect(self.db) as con:
            expected = con.execute("""
                SELECT SUM(ROUND(i.quantity * i.unit_price, 2))
                FROM order_items i JOIN orders o ON i.order_id=o.order_id
                WHERE o.status='Completed'
            """).fetchone()[0]
        self.assertAlmostEqual(sales_kpis(self.sales)["revenue"], expected, places=2)

    def test_generated_database_integrity(self):
        self.assertTrue(all(v == 0 for v in database_integrity(self.db).values()))
        self.assertTrue(all(v == 0 for v in data_quality(self.sales).values()))

if __name__ == "__main__":
    unittest.main()
