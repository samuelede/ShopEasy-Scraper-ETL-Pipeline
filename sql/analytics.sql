\echo 'QUERY 1: Current Price Overview'
SELECT product_name, category, price, rating, in_stock
FROM books.books ORDER BY price DESC LIMIT 20;

\echo 'QUERY 2: Overpriced and Underpriced Books'
WITH s AS (SELECT category, AVG(price) a, STDDEV(price) d FROM books.books GROUP BY category)
SELECT b.product_name, b.category, b.price, ROUND(s.a::NUMERIC,2) AS avg,
CASE WHEN b.price > s.a+1.5*s.d THEN 'OVERPRICED'
     WHEN b.price < s.a-1.5*s.d THEN 'UNDERPRICED' ELSE 'FAIR' END AS band
FROM books.books b JOIN s USING (category) ORDER BY band, b.category, b.price DESC;

\echo 'QUERY 3: Category Price Variation'
SELECT category, COUNT(*) AS books,
ROUND(AVG(price)::NUMERIC,2) AS avg, ROUND(MIN(price)::NUMERIC,2) AS min,
ROUND(MAX(price)::NUMERIC,2) AS max, ROUND(STDDEV(price)::NUMERIC,2) AS stddev
FROM books.books GROUP BY category ORDER BY stddev DESC;

\echo 'QUERY 4: Best Value Books'
SELECT product_name, category, price, rating,
ROUND((rating::NUMERIC / NULLIF(price::NUMERIC,0) * 10),2) AS value_score
FROM books.books WHERE rating > 0 AND price > 0
ORDER BY value_score DESC LIMIT 20;

\echo 'QUERY 5: Average Price per Star Rating'
SELECT rating, COUNT(*) AS books,
ROUND(AVG(price)::NUMERIC,2) AS avg_price,
ROUND(MIN(price)::NUMERIC,2) AS min_price,
ROUND(MAX(price)::NUMERIC,2) AS max_price
FROM books.books WHERE rating > 0 GROUP BY rating ORDER BY rating DESC;

\echo 'QUERY 6: Stock Availability by Category'
SELECT category, COUNT(*) AS total,
SUM(CASE WHEN in_stock THEN 1 ELSE 0 END) AS in_stock,
SUM(CASE WHEN NOT in_stock THEN 1 ELSE 0 END) AS out_of_stock,
ROUND(SUM(CASE WHEN NOT in_stock THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100,1) AS pct_out
FROM books.books GROUP BY category ORDER BY pct_out DESC;

\echo 'QUERY 7: Pipeline Summary'
SELECT COUNT(*) AS total_books, COUNT(DISTINCT category) AS categories,
ROUND(AVG(price)::NUMERIC,2) AS avg_price,
ROUND(MIN(price)::NUMERIC,2) AS cheapest,
ROUND(MAX(price)::NUMERIC,2) AS most_expensive,
SUM(CASE WHEN in_stock THEN 1 ELSE 0 END) AS in_stock_count
FROM books.books;