# ecommerce-query-optimizer-demo

A small, self-contained project that demonstrates **why e-commerce databases slow
down under load and how indexing fixes it**. It seeds a realistic SQLite database,
runs the kinds of queries a storefront fires on every page (multi-parameter product
filtering, user order history, checkout look-ups), and measures them **before and
after** adding the right indexes.

Everything runs with the Python standard library plus `pytest` — **no database
server to install**.

## Why this project exists

As an online store grows, the same SQL that felt instant with a few hundred
products starts to crawl once the catalog and traffic grow. The usual culprits are
full table scans on unindexed columns, inefficient joins, and poorly ordered
predicates. This repo makes that slowdown visible and then fixes it, so you can see
the impact of each change rather than take it on faith.

## What it shows

Running the benchmark on a 100,000-product / 50,000-order dataset produces results
like this (numbers vary by machine):

| Query | Before indexing | After indexing | Speedup |
|-------|-----------------|----------------|---------|
| Product filter (category + price + rating) | ~9.4 ms | ~0.07 ms | **~140x** |
| User order history (join) | ~13.5 ms | ~0.06 ms | **~240x** |
| Keyword search `LIKE '%term%'` | fast but still a scan | still a scan | ~1x |

The query plans flip from `SCAN products` to
`SEARCH products USING INDEX ...`, which is the whole point. The keyword search
*deliberately* does not improve, because a leading-wildcard `LIKE` cannot use a
B-tree index — see [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) for why and what to do
instead.

## Quick start

```bash
# 1. (optional) install dev tools for tests and linting
pip install -r requirements.txt

# 2. build the mock database (writes ./ecommerce.db)
python src/seed.py

# 3. benchmark the queries before and after indexing
python src/benchmark.py

# 4. run the test suite
pytest -q
```

To apply the indexes manually and poke around with the SQLite CLI:

```bash
sqlite3 ecommerce.db < sql/indexes.sql
sqlite3 ecommerce.db "EXPLAIN QUERY PLAN SELECT * FROM products WHERE category_id = 3;"
```

## Project layout

```
.
├── src/
│   ├── seed.py          # generates the mock dataset
│   ├── queries.py       # the hot-path SQL under test
│   └── benchmark.py     # times queries before/after indexing + prints plans
├── sql/
│   └── indexes.sql      # the composite + single-column indexes
├── tests/
│   └── test_queries.py  # correctness + "scan becomes search" checks
├── .github/workflows/
│   └── ci.yml           # GitHub Actions: lint + test on every push/PR
├── TROUBLESHOOTING.md   # how to diagnose slow queries step by step
└── CONTRIBUTING.md      # branching strategy + PR workflow
```

## How this maps to the coursework

- **Database performance & optimization (Scenario 2):** `seed.py`, `queries.py`,
  `benchmark.py`, and `sql/indexes.sql` show how to find bottlenecks with query
  plans and fix them with composite B-tree indexes.
- **Collaboration & CI/CD (Scenario 1):** [`CONTRIBUTING.md`](CONTRIBUTING.md)
  documents the Git branching strategy, and
  [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs the tests
  automatically on every pull request.

## License

[MIT](LICENSE)
