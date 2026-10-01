# Troubleshooting slow queries

A step-by-step method for finding and fixing the kind of database slowdown this
repo demonstrates. The commands use SQLite, but the *approach* is the same in
PostgreSQL and MySQL — the equivalent tools are noted at the end.

## 1. Reproduce and measure before changing anything

Never optimize by guessing. Build the dataset and run the benchmark so you have a
baseline number to beat:

```bash
python src/seed.py
python src/benchmark.py
```

Record the "before" timings. Any change you make should be judged against them.

## 2. Read the query plan

The single most useful tool is the planner's own explanation of how it will run a
query. In SQLite:

```sql
EXPLAIN QUERY PLAN
SELECT id, name, price, rating
FROM products
WHERE category_id = 3 AND price BETWEEN 50 AND 500 AND rating >= 4.0
ORDER BY price ASC
LIMIT 20;
```

Interpreting the output:

- **`SCAN products`** — the engine reads *every row* in the table and tests the
  predicate on each. This is O(n) and is the main cause of the slowdown here.
- **`SEARCH products USING INDEX ...`** — the engine seeks directly into a B-tree
  index, which is roughly O(log n). This is the goal.
- **`USE TEMP B-TREE FOR ORDER BY`** — the engine had to build a throwaway
  structure just to sort the results, extra work an index can often remove.

## 3. Identify the most expensive queries

- **SQLite:** run `.timer on` in the `sqlite3` shell, or use the `time_query`
  helper in `src/benchmark.py`, which averages each query over many runs to cut
  noise.
- Look for the queries that are both slow *and* frequent. A 9 ms query fired on
  every product-list page hurts far more than a 2 second report run once a day.

## 4. Fix the bottleneck

The most common fixes, in rough order of impact:

1. **Add an index that matches the WHERE clause.** For the multi-parameter filter,
   a single composite index on `(category_id, price, rating)` covers the equality
   predicate first, then the range, then the final narrowing column. See
   `sql/indexes.sql`.
2. **Order composite-index columns correctly:** equality columns first, then the
   range column, then columns used only for further filtering or sorting. The wrong
   order means the index can only partly be used.
3. **Index foreign keys used in joins** (`orders.user_id`,
   `order_items.order_id`) so joins become index seeks instead of scans.
4. **Keep write transactions short** at checkout and rely on row-level locking so
   concurrent shoppers do not queue behind one another.
5. **Cache hot, rarely changing reads** (for example, the top product listings) so
   repeated identical requests never reach the database at all.

## 5. The leading-wildcard LIKE trap

```sql
SELECT * FROM products WHERE name LIKE '%Smart%';   -- cannot use a B-tree index
```

A `%` at the *start* of the pattern means the engine cannot seek into the index, so
it scans regardless of how many indexes exist. That is why the keyword search in
the benchmark does not speed up. The real fixes are a **full-text search index**
(`FTS5` in SQLite, `tsvector`/GIN in PostgreSQL, `FULLTEXT` in MySQL) or a dedicated
search engine such as Elasticsearch.

## 6. Re-measure

Run `python src/benchmark.py` again and compare against the baseline from step 1.
Confirm the plan now says `SEARCH ... USING INDEX` and that the timing actually
dropped. Optimization is only "done" when the numbers prove it.

## Equivalent tools in other databases

| Task | SQLite | PostgreSQL | MySQL |
|------|--------|------------|-------|
| See the plan | `EXPLAIN QUERY PLAN` | `EXPLAIN ANALYZE` | `EXPLAIN ANALYZE` |
| Find slow queries | `.timer on` | `pg_stat_statements`, slow-query log | slow query log |
| Refresh statistics | `ANALYZE` | `ANALYZE` | `ANALYZE TABLE` |
| Full-text search | `FTS5` | `tsvector` + GIN index | `FULLTEXT` index |
