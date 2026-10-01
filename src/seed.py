"""Generate a deterministic mock e-commerce dataset in SQLite.

Creates categories, users, products, orders, and order_items tables and
populates them with enough rows that unindexed queries become measurably
slow. Running this script is the first step in the optimization demo.

Usage:
    python src/seed.py                # writes ./ecommerce.db
    python src/seed.py --db test.db   # custom path
    python src/seed.py --products 50000
"""

import argparse
import os
import random
import sqlite3

# A fixed seed keeps the generated data reproducible across runs and machines,
# so benchmark numbers are comparable.
RANDOM_SEED = 42

CATEGORIES = [
    "Electronics", "Books", "Home & Kitchen", "Clothing", "Toys",
    "Sports", "Beauty", "Automotive", "Garden", "Office",
]

ADJECTIVES = ["Premium", "Classic", "Eco", "Smart", "Portable",
              "Wireless", "Compact", "Deluxe", "Ultra", "Basic"]
NOUNS = ["Widget", "Gadget", "Stand", "Charger", "Bottle",
         "Lamp", "Backpack", "Monitor", "Speaker", "Organizer"]


def build_schema(conn):
    """Create tables from scratch, dropping any that already exist."""
    conn.executescript(
        """
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS categories;

        CREATE TABLE categories (
            id   INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE users (
            id         INTEGER PRIMARY KEY,
            email      TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE products (
            id          INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            price       REAL NOT NULL,
            rating      REAL NOT NULL,
            stock       INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE orders (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            total      REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE order_items (
            id         INTEGER PRIMARY KEY,
            order_id   INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity   INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        """
    )


def seed(db_path, n_products=100000, n_users=10000, n_orders=50000):
    rng = random.Random(RANDOM_SEED)

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    try:
        build_schema(conn)

        conn.executemany(
            "INSERT INTO categories (id, name) VALUES (?, ?)",
            [(i + 1, name) for i, name in enumerate(CATEGORIES)],
        )

        users = [
            (uid, "user{}@example.com".format(uid),
             "2024-{:02d}-{:02d}".format(rng.randint(1, 12), rng.randint(1, 28)))
            for uid in range(1, n_users + 1)
        ]
        conn.executemany(
            "INSERT INTO users (id, email, created_at) VALUES (?, ?, ?)", users
        )

        products = []
        for pid in range(1, n_products + 1):
            name = "{} {} {}".format(
                rng.choice(ADJECTIVES), rng.choice(NOUNS), pid
            )
            products.append((
                pid,
                name,
                rng.randint(1, len(CATEGORIES)),
                round(rng.uniform(5.0, 2000.0), 2),
                round(rng.uniform(1.0, 5.0), 1),
                rng.randint(0, 500),
            ))
        conn.executemany(
            "INSERT INTO products (id, name, category_id, price, rating, stock) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            products,
        )

        orders = [
            (oid, rng.randint(1, n_users),
             "2024-{:02d}-{:02d}".format(rng.randint(1, 12), rng.randint(1, 28)),
             round(rng.uniform(10.0, 5000.0), 2))
            for oid in range(1, n_orders + 1)
        ]
        conn.executemany(
            "INSERT INTO orders (id, user_id, created_at, total) VALUES (?, ?, ?, ?)",
            orders,
        )

        order_items = []
        item_id = 1
        for oid in range(1, n_orders + 1):
            for _ in range(rng.randint(1, 4)):
                order_items.append((
                    item_id, oid, rng.randint(1, n_products), rng.randint(1, 5)
                ))
                item_id += 1
        conn.executemany(
            "INSERT INTO order_items (id, order_id, product_id, quantity) "
            "VALUES (?, ?, ?, ?)",
            order_items,
        )

        conn.commit()
        print("Seeded {}: {} products, {} users, {} orders, {} order items".format(
            db_path, n_products, n_users, n_orders, len(order_items)
        ))
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Seed a mock e-commerce SQLite database.")
    parser.add_argument("--db", default="ecommerce.db", help="Output database path")
    parser.add_argument("--products", type=int, default=100000)
    parser.add_argument("--users", type=int, default=10000)
    parser.add_argument("--orders", type=int, default=50000)
    args = parser.parse_args()
    seed(args.db, args.products, args.users, args.orders)


if __name__ == "__main__":
    main()
