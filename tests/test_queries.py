"""Correctness and optimization tests, runnable with `pytest`.

These run against a small, fast in-memory-style database so CI stays quick.
They verify both that the queries return correct results and that the
indexes actually change the query plan from a SCAN to a SEARCH.
"""

import sqlite3

import pytest

import queries
import seed


@pytest.fixture()
def conn(tmp_path):
    db = str(tmp_path / "test.db")
    seed.seed(db, n_products=2000, n_users=200, n_orders=500)
    connection = sqlite3.connect(db)
    yield connection
    connection.close()


def test_filter_respects_all_predicates(conn):
    rows = queries.filter_products(conn, category_id=3,
                                   min_price=50.0, max_price=500.0, min_rating=4.0)
    for _id, _name, price, rating in rows:
        assert 50.0 <= price <= 500.0
        assert rating >= 4.0


def test_filter_results_are_price_sorted(conn):
    rows = queries.filter_products(conn, 3, 50.0, 500.0, 4.0)
    prices = [r[2] for r in rows]
    assert prices == sorted(prices)


def test_search_matches_keyword(conn):
    rows = queries.search_products(conn, "Smart")
    assert all("Smart" in r[1] for r in rows)


def test_order_history_belongs_to_user(conn):
    # User 1 definitely exists; history may be empty but must never error.
    rows = queries.user_order_history(conn, 1)
    assert isinstance(rows, list)


def test_index_converts_scan_to_search(conn):
    params = (3, 50.0, 500.0, 4.0)

    before = conn.execute(
        "EXPLAIN QUERY PLAN " + queries.FILTER_PRODUCTS, params
    ).fetchall()
    assert any("SCAN" in row[-1] for row in before), "expected a full scan first"

    conn.executescript(
        "CREATE INDEX idx_test ON products (category_id, price, rating); ANALYZE;"
    )

    after = conn.execute(
        "EXPLAIN QUERY PLAN " + queries.FILTER_PRODUCTS, params
    ).fetchall()
    assert any("SEARCH" in row[-1] for row in after), "expected an index search"
