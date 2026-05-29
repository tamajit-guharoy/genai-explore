"""
10_dlt_ingestion.py — Build a knowledge graph from a relational database.

This example demonstrates the pattern of extracting data from a SQL database
and building a knowledge graph where table rows become entities and foreign
keys become relationships.

For the actual DLT integration (direct Postgres/MySQL/BigQuery ingestion),
Cognee uses the dlt library. This example uses SQLite to illustrate the
concept without external database dependencies.

Prerequisites:
    pip install cognee
"""

import asyncio
import sqlite3
import json

import cognee


async def main():
    # ── Step 1: Create a sample database ───────────────────────────────
    print("Setting up sample product database...")

    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT,
            reliability_score REAL
        );

        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category_id INTEGER REFERENCES categories(id),
            supplier_id INTEGER REFERENCES suppliers(id),
            price REAL,
            stock_quantity INTEGER,
            discontinued BOOLEAN DEFAULT FALSE
        );

        INSERT INTO categories VALUES (1, 'Electronics', 'Electronic devices and components');
        INSERT INTO categories VALUES (2, 'Furniture', 'Office and home furniture');
        INSERT INTO categories VALUES (3, 'Software', 'Software licenses and subscriptions');

        INSERT INTO suppliers VALUES (1, 'TechSupply GmbH', 'Germany', 98.5);
        INSERT INTO suppliers VALUES (2, 'GlobalParts Ltd', 'Taiwan', 92.0);
        INSERT INTO suppliers VALUES (3, 'NordicWood AS', 'Norway', 95.0);

        INSERT INTO products VALUES (1, 'Laptop Pro 15', 1, 1, 1299.99, 500, FALSE);
        INSERT INTO products VALUES (2, 'USB-C Hub', 1, 2, 49.99, 2000, FALSE);
        INSERT INTO products VALUES (3, 'Standing Desk', 2, 3, 799.00, 150, FALSE);
        INSERT INTO products VALUES (4, 'Office Monitor 27"', 1, 2, 449.00, 300, FALSE);
        INSERT INTO products VALUES (5, 'Antivirus Suite', 3, 1, 79.99, 9999, FALSE);
    """)

    # ── Step 2: Extract data and convert to text for Cognee ────────────
    print("Extracting data from database...")

    # In a real DLT integration, this is handled automatically.
    # Here we manually transform the relational data into descriptive text.
    rows = conn.execute("""
        SELECT p.name AS product, p.price, p.stock_quantity, p.discontinued,
               c.name AS category, c.description AS category_desc,
               s.name AS supplier, s.country, s.reliability_score
        FROM products p
        JOIN categories c ON p.category_id = c.id
        JOIN suppliers s ON p.supplier_id = s.id
    """).fetchall()

    product_descriptions = []
    for row in rows:
        product, price, stock, disc, cat, cat_desc, supplier, country, rel = row
        status = "discontinued" if disc else "active"
        product_descriptions.append(
            f"Product: {product} (${price:.2f}) — Status: {status}, "
            f"Stock: {stock} units. "
            f"Category: {cat} — {cat_desc}. "
            f"Supplier: {supplier} ({country}, reliability: {rel}%)."
        )

    full_text = "\n".join(product_descriptions)

    # ── Step 3: Build knowledge graph ──────────────────────────────────
    print("Building knowledge graph with entity relationships from DB schema...")
    await cognee.add(full_text, dataset_name="product_catalog")
    await cognee.cognify()

    # ── Step 4: Query across relationships ─────────────────────────────
    print("\n" + "=" * 60)
    print("Supply chain queries:")

    queries = [
        "Which products are supplied by Taiwanese companies?",
        "What products in the Electronics category are active and in stock?",
        "Which supplier provides the most products and what is their reliability?",
        "Are there any discontinued products?",
    ]

    for query in queries:
        print(f"\n Q: {query}")
        print("-" * 40)
        results = await cognee.search(query)
        for r in results:
            print(f"  → {r}")
        print()

    # ── Bonus: The FK relationships become graph edges ─────────────────
    print("=" * 60)
    print("In a full DLT integration, foreign keys automatically become graph edges:")
    print("  Product -[belongs_to]-> Category")
    print("  Product -[supplied_by]-> Supplier")
    print("This enables multi-hop queries like:")
    print("  'Find suppliers in countries with trade restrictions who supply")
    print("   products in categories that have low stock.'")

    conn.close()


if __name__ == "__main__":
    asyncio.run(main())
