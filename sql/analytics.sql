-- =============================================================================
-- ShopEasy - Web Scraping Data Pipeline & Price Intelligence Analytics
-- Database: shopeasy | Schema: books | Table: books.books
-- =============================================================================

\echo '================================================================='
\echo ' ShopEasy Price Intelligence Analytics'
\echo ' Database: shopeasy | Table: books.books'
\echo '================================================================='
\echo ''


-- 1. CURRENT PRICE OVERVIEW
\echo '-----------------------------------------------------------------'
\echo ' QUERY 1: Current Price Overview (Top 20 Most Expensive Books)'
\echo '-----------------------------------------------------------------'

SELECT
    product_name,
    category,
    price,
    rating,
    in_stock
FROM books.books
ORDER BY price DESC
LIMIT 20;


-- 2. OVERPRICED & UNDERPRICED BOOKS
\echo '-----------------------------------------------------------------'
\echo ' QUERY 2: Overpriced and Underpriced Books vs Category Average'
\echo '-----------------------------------------------------------------'

WITH category_stats AS (
    SELECT
        category,
        AVG(price)    AS avg_price,
        STDDEV(price) AS std_price
    FROM books.books
    GROUP BY category
)
SELECT
    b.product_name,
    b.category,
    b.price,
    ROUND(cs.avg_price::NUMERIC, 2) AS category_avg,
    CASE
        WHEN b.price > cs.avg_price + 1.5 * cs.std_price THEN 'OVERPRICED'
        WHEN b.price < cs.avg_price - 1.5 * cs.std_price THEN 'UNDERPRICED'
        ELSE 'FAIR'
    END AS price_band
FROM books.books b
JOIN category_stats cs USING (category)
ORDER BY price_band, b.category, b.price DESC;


-- 3. CATEGORY PRICE VARIATION
\echo '-----------------------------------------------------------------'
\echo ' QUERY 3: Category Price Variation (Highest Inconsistency First)'
\echo '-----------------------------------------------------------------'

SELECT
    category,
    COUNT(*)                                    AS total_books,
    ROUND(AVG(price)::NUMERIC, 2)               AS avg_price,
    ROUND(MIN(price)::NUMERIC, 2)               AS min_price,
    ROUND(MAX(price)::NUMERIC, 2)               AS max_price,
    ROUND(STDDEV(price)::NUMERIC, 2)            AS price_stddev
FROM books.books
GROUP BY category
ORDER BY price_stddev DESC;


-- 4. BEST VALUE BOOKS
\echo '-----------------------------------------------------------------'
\echo ' QUERY 4: Best Value Books (High Rating, Low Price - Top 20)'
\echo '-----------------------------------------------------------------'

SELECT
    product_name,
    category,
    price,
    rating,
    ROUND((rating::NUMERIC / NULLIF(price::NUMERIC, 0) * 10), 2) AS value_score
FROM books.books
WHERE rating > 0 AND price > 0
ORDER BY value_score DESC
LIMIT 20;


-- 5. AVERAGE PRICE PER RATING
\echo '-----------------------------------------------------------------'
\echo ' QUERY 5: Average Price per Star Rating'
\echo '-----------------------------------------------------------------'

SELECT
    rating,
    COUNT(*)                                    AS total_books,
    ROUND(AVG(price)::NUMERIC, 2)               AS avg_price,
    ROUND(MIN(price)::NUMERIC, 2)               AS min_price,
    ROUND(MAX(price)::NUMERIC, 2)               AS max_price
FROM books.books
WHERE rating > 0
GROUP BY rating
ORDER BY rating DESC;


-- 6. OUT OF STOCK SUMMARY BY CATEGORY
\echo '-----------------------------------------------------------------'
\echo ' QUERY 6: Stock Availability by Category'
\echo '-----------------------------------------------------------------'

SELECT
    category,
    COUNT(*)                                                        AS total_books,
    SUM(CASE WHEN in_stock THEN 1 ELSE 0 END)                      AS in_stock,
    SUM(CASE WHEN NOT in_stock THEN 1 ELSE 0 END)                  AS out_of_stock,
    ROUND(
        SUM(CASE WHEN NOT in_stock THEN 1 ELSE 0 END)::NUMERIC
        / COUNT(*) * 100, 1
    )                                                               AS out_of_stock_pct
FROM books.books
GROUP BY category
ORDER BY out_of_stock_pct DESC;


-- 7. PIPELINE SUMMARY
\echo '-----------------------------------------------------------------'
\echo ' QUERY 7: Pipeline Summary - Overall Stats'
\echo '-----------------------------------------------------------------'

SELECT
    COUNT(*)                                    AS total_books,
    COUNT(DISTINCT category)                    AS total_categories,
    ROUND(AVG(price)::NUMERIC, 2)               AS avg_price,
    ROUND(MIN(price)::NUMERIC, 2)               AS cheapest,
    ROUND(MAX(price)::NUMERIC, 2)               AS most_expensive,
    SUM(CASE WHEN in_stock THEN 1 ELSE 0 END)   AS in_stock_count
FROM books.books;

\echo ''
\echo '================================================================='
\echo ' Analytics Complete'
\echo '================================================================='