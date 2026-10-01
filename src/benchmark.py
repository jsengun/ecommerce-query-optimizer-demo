"""Measure query latency before and after indexing, and show the query plans.

This is the headline script. It runs the hot-path queries against the seeded
database, applies the indexes from sql/indexes.sql, re-runs the same queries,
and prints a before/after comparison together with the EXPLAIN QUERY PLAN
output so you can see SCAN turn into SEARCH.

Usage:
    python src/seed.py            # once, to build ecommerce.db
    python src/benchmark.py       # then benchmark it
"""

import argparse
import os
import sqlite3
import time

import queries

# Representative parameters for each query.
FILTER_ARGS = (3, 50.0, 500.0, 4.0)   # category, price range, min rating
SEARCH_ARG = "Smart"
USER_ARG = 1234
REPEATS = 50                          # average over several runs to reduce noise

HERE = os.path.dirname(os.path.abspath(__file__))
INDEXES_SQL = os.path.join(HERE, "..", "sql", "indexes.sql")


def time_query(conn, fn, *args):
    """Return the average wall-clock milliseconds over REPEATS executions."""
    start = time.perf_counter()
    for _ in range(REPEATS):
        fn(conn, *args)
    elapsed = time.perf_counter() - start
    return (elapsed / REPEATS) * 1000.0


def explain(conn, sql, params):
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    return "; ".join(r[-1] for r in rows)


def run_suite(conn, label):
    print("\n=== {} ===".format(label))
    results = {}

    results["filter"] = time_query(conn, queries.filter_products, *FILTER_ARGS)
    print("  product filter       : {:7.3f} ms   plan: {}".format(
        results["filter"],
        explain(conn, queries.FILTER_PRODUCTS, FILTER_ARGS)))

    results["history"] = time_query(conn, queries.user_order_history, USER_ARG)
    print("  user order history   : {:7.3f} ms   plan: {}".format(
        results["history"],
        explain(conn, queries.USER_ORDER_HISTORY, (USER_ARG,))))

    results["search"] = time_query(conn, queries.search_products, SEARCH_ARG)
    print("  keyword search (LIKE): {:7.3f} ms   plan: {}".format(
        results["search"],
        explain(conn, queries.SEARCH_PRODUCTS, ("%" + SEARCH_ARG + "%",))))

    return results


def apply_indexes(conn):
    with open(INDEXES_SQL) as fh:
        conn.executescript(fh.read())


def main():
    parser = argparse.ArgumentParser(description="Benchmark e-commerce queries.")
    parser.add_argument("--db", default="ecommerce.db")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        raise SystemExit(
            "Database '{}' not found. Run `python src/seed.py` first.".format(args.db)
        )

    conn = sqlite3.connect(args.db)
    try:
        before = run_suite(conn, "BEFORE indexing")
        apply_indexes(conn)
        after = run_suite(conn, "AFTER indexing")

        print("\n=== SPEEDUP ===")
        for key in ("filter", "history", "search"):
            b, a = before[key], after[key]
            factor = (b / a) if a > 0 else float("inf")
            print("  {:<20}: {:7.3f} ms -> {:7.3f} ms  ({:.1f}x faster)".format(
                key, b, a, factor))
        print("\nNote: the LIKE '%keyword%' search barely improves because a "
              "leading wildcard cannot use a B-tree index. See TROUBLESHOOTING.md.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
