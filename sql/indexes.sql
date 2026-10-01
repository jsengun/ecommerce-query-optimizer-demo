-- Indexes that turn full table scans into logarithmic B-tree lookups.
-- Apply after seeding:  sqlite3 ecommerce.db < sql/indexes.sql
-- SQLite builds B-tree indexes by default, so these give O(log n) seeks
-- plus efficient range scans instead of O(n) scans of every product row.

-- Composite index for the multi-parameter product filter.
-- Column order matters: the equality predicate (category_id) comes first so
-- SQLite can seek straight to the category, then range-scan price, then use
-- rating to narrow further. This single index serves the whole WHERE clause.
CREATE INDEX IF NOT EXISTS idx_products_cat_price_rating
    ON products (category_id, price, rating);

-- Speeds up the user order-history join and its WHERE user_id = ? lookup.
CREATE INDEX IF NOT EXISTS idx_orders_user
    ON orders (user_id);

-- Supports the JOIN from orders to their line items.
CREATE INDEX IF NOT EXISTS idx_order_items_order
    ON order_items (order_id);

-- Refresh the planner's statistics so it chooses the new indexes.
ANALYZE;
