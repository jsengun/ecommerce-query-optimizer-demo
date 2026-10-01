"""The SQL queries whose performance this demo measures and optimizes.

These mirror the three hot paths called out in the assignment scenario:
multi-parameter product search/filtering, a user's order history (a join),
and the read side of checkout (looking up a product before updating stock).

Each query is kept as a named constant so the same text can be timed by
benchmark.py, inspected with EXPLAIN QUERY PLAN, and asserted in tests.
"""

# Multi-parameter filter: the star of the demo. Without a supporting index,
# SQLite must scan every product row and test each predicate.
FILTER_PRODUCTS = """
SELECT id, name, price, rating
FROM products
WHERE category_id = ?
  AND price BETWEEN ? AND ?
  AND rating >= ?
ORDER BY price ASC
LIMIT 20
"""

# Keyword search on the product name. A leading-wildcard LIKE cannot use a
# normal B-tree index, which is itself a useful lesson in the TROUBLESHOOTING notes.
SEARCH_PRODUCTS = """
SELECT id, name, price, rating
FROM products
WHERE name LIKE ?
LIMIT 20
"""

# Order history for one user, joined to the items. Benefits from an index on
# orders.user_id and order_items.order_id.
USER_ORDER_HISTORY = """
SELECT o.id, o.created_at, o.total, oi.product_id, oi.quantity
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
WHERE o.user_id = ?
ORDER BY o.created_at DESC
"""

# Checkout read path: fetch a product's price and stock before writing.
PRODUCT_FOR_CHECKOUT = """
SELECT id, price, stock
FROM products
WHERE id = ?
"""


def filter_products(conn, category_id, min_price, max_price, min_rating):
    return conn.execute(
        FILTER_PRODUCTS, (category_id, min_price, max_price, min_rating)
    ).fetchall()


def search_products(conn, keyword):
    return conn.execute(SEARCH_PRODUCTS, ("%" + keyword + "%",)).fetchall()


def user_order_history(conn, user_id):
    return conn.execute(USER_ORDER_HISTORY, (user_id,)).fetchall()
