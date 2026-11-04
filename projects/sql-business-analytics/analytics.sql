-- Run after: python generate_data.py
-- Revenue includes only completed orders.
.headers on
.mode column

-- 1. Monthly revenue and completed orders
SELECT strftime('%Y-%m', o.order_date) AS month,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
       COUNT(DISTINCT o.order_id) AS orders
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'Completed'
GROUP BY strftime('%Y-%m', o.order_date)
ORDER BY month;

-- 2. Revenue by category
SELECT p.category,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
       SUM(oi.quantity) AS units_sold
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status = 'Completed'
GROUP BY p.category
ORDER BY revenue DESC;

-- 3. Top 10 products
SELECT p.product_name,
       p.category,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status = 'Completed'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;

-- 4. Repeat customers (two or more completed orders)
WITH completed_orders AS (
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    WHERE status = 'Completed'
    GROUP BY customer_id
)
SELECT COUNT(*) AS repeat_customers
FROM completed_orders
WHERE order_count >= 2;

-- 5. Average order value (not average line value)
WITH order_totals AS (
    SELECT o.order_id, SUM(oi.quantity * oi.unit_price) AS order_revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY o.order_id
)
SELECT ROUND(AVG(order_revenue), 2) AS average_order_value
FROM order_totals;
