"""Generate deterministic synthetic retail data for the dashboard."""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB = Path(__file__).with_name("retail_analytics.db")
SEED = 2026

PRODUCTS = [
    ("Wireless Mouse", "Electronics", 24.99),
    ("USB-C Hub", "Electronics", 39.99),
    ("Laptop Stand", "Electronics", 32.50),
    ("Notebook", "Office", 6.99),
    ("Gel Pen Set", "Office", 11.50),
    ("Desk Organizer", "Office", 18.75),
    ("Water Bottle", "Lifestyle", 19.99),
    ("Canvas Tote", "Lifestyle", 14.50),
    ("Travel Mug", "Lifestyle", 22.00),
    ("Yoga Mat", "Fitness", 28.00),
    ("Resistance Bands", "Fitness", 16.00),
    ("Jump Rope", "Fitness", 12.00),
]


def main():
    rng = random.Random(SEED)
    with sqlite3.connect(DB) as con:
        con.executescript("""
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            segment TEXT NOT NULL,
            region TEXT NOT NULL
        );
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_price REAL NOT NULL CHECK(unit_price >= 0)
        );
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
            order_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Completed', 'Canceled'))
        );
        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(order_id),
            product_id INTEGER NOT NULL REFERENCES products(product_id),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0)
        );
        CREATE INDEX idx_orders_date ON orders(order_date);
        CREATE INDEX idx_orders_customer ON orders(customer_id);
        CREATE INDEX idx_items_order ON order_items(order_id);
        """)
        con.executemany(
            "INSERT INTO products(product_name, category, unit_price) VALUES (?, ?, ?)",
            PRODUCTS,
        )
        regions = ["Northeast", "South", "Midwest", "West"]
        segments = ["Consumer", "Small Business", "Student"]
        con.executemany(
            "INSERT INTO customers(customer_id, segment, region) VALUES (?, ?, ?)",
            [(i, rng.choice(segments), rng.choice(regions)) for i in range(1, 251)],
        )
        start = date(2025, 1, 1)
        orders = []
        items = []
        item_id = 1
        for order_id in range(1, 1501):
            order_date = start + timedelta(days=rng.randrange(0, 730))
            status = "Canceled" if rng.random() < 0.07 else "Completed"
            orders.append((order_id, rng.randint(1, 250), order_date.isoformat(), status))
            for product_id in rng.sample(range(1, len(PRODUCTS) + 1), rng.randint(1, 4)):
                price = PRODUCTS[product_id - 1][2]
                items.append((item_id, order_id, product_id, rng.randint(1, 4), price))
                item_id += 1
        con.executemany(
            "INSERT INTO orders(order_id, customer_id, order_date, status) VALUES (?, ?, ?, ?)",
            orders,
        )
        con.executemany(
            "INSERT INTO order_items(order_item_id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
            items,
        )
    print(f"Created {DB} with {len(orders)} orders and {len(items)} order lines.")


if __name__ == "__main__":
    main()
