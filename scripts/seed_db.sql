-- Seed script for messy ecommerce database schema
-- Messy characteristics:
-- 1. Ambiguous Keys: customers PK is customer_id; orders FK is cust_id (mismatch)
-- 2. Denormalization: orders has total_amount; line_items has qty and unit_price
-- 3. Nullable Columns: customers.region allows NULL values
-- 4. High Data Volume: 120 customers, 600 orders, 1800 line items

DROP TABLE IF EXISTS line_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    region VARCHAR(100) NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    cust_id INTEGER REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL
);

CREATE TABLE line_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_name VARCHAR(255) NOT NULL,
    qty INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

-- Seed 120 customers with some nullable regions
INSERT INTO customers (name, region)
SELECT 
    'Customer ' || i AS name,
    CASE 
        WHEN i % 6 = 0 THEN NULL
        WHEN i % 5 = 1 THEN 'North'
        WHEN i % 5 = 2 THEN 'South'
        WHEN i % 5 = 3 THEN 'East'
        WHEN i % 5 = 4 THEN 'West'
        ELSE 'Central'
    END AS region
FROM generate_series(1, 120) AS i;

-- Seed 600 orders
INSERT INTO orders (cust_id, order_date, total_amount)
SELECT 
    ((i * 7 + 3) % 120) + 1 AS cust_id,
    DATE '2024-01-01' + ((i * 3) % 365) * INTERVAL '1 day' AS order_date,
    ROUND((20 + (i * 13) % 450 + (i % 10) * 0.75)::numeric, 2) AS total_amount
FROM generate_series(1, 600) AS i;

-- Seed 1800 line items (~3 per order)
INSERT INTO line_items (order_id, product_name, qty, unit_price)
SELECT 
    ((i - 1) / 3) + 1 AS order_id,
    CASE (i % 8)
        WHEN 0 THEN 'Laptop'
        WHEN 1 THEN 'Wireless Mouse'
        WHEN 2 THEN 'Mechanical Keyboard'
        WHEN 3 THEN '4K Monitor'
        WHEN 4 THEN 'USB-C Cable'
        WHEN 5 THEN 'Noise Cancelling Headphones'
        WHEN 6 THEN 'Ergonomic Chair'
        ELSE 'Desk Lamp'
    END AS product_name,
    ((i % 5) + 1) AS qty,
    ROUND((15 + (i * 17) % 200 + (i % 3) * 0.99)::numeric, 2) AS unit_price
FROM generate_series(1, 1800) AS i;
