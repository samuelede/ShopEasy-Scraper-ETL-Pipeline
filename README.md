# ShopEasy — Web Scraping Data Pipeline & Price Intelligence Analytics

A production-grade ETL pipeline built for **ShopEasy Retail Intelligence** that automates data
collection from [books.toscrape.com](https://books.toscrape.com), transforms it into clean,
structured records, and loads it into a PostgreSQL database to enable pricing analytics and
market trend monitoring.

---

## Project Structure

```
ShopEasy-Scraper-ETL-Pipeline/
├── python/
│   ├── __init__.py
│   ├── config.py          # Database credentials and scraper settings
│   ├── logger.py          # Logging setup (console + file)
│   ├── extract_books.py   # Scrapes books.toscrape.com in batches
│   ├── transform.py       # Cleans prices, ratings, removes bad rows
│   ├── load.py            # Inserts cleaned data into PostgreSQL
│   └── pipeline.py        # Runs all three steps in order
│
├── sql/
│   ├── create_table.py    # Run once to set up the database table
│   └── analytics.sql      # Price intelligence queries
│
├── data/
│   └── logs/
│       ├── app.log        # Pipeline activity log (auto-created)
│       └── scheduler.log  # Scheduled run history (auto-created)
│
├── run_pipeline.bat       # Windows Task Scheduler automation script
├── .env                   # Your database credentials (never commit this)
└── requirements.txt
```

---

## Prerequisites

- Python 3.11+
- PostgreSQL 14+

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourhandle/books-pipeline.git
cd books-pipeline
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your environment variables

Create a `.env` file in the project root:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=shopeasy
DB_USER=postgres
DB_PASSWORD=your_password_here

SCRAPE_DELAY=1.5
```

### 5. Create the database table (once only)

Make sure the `shopeasy` database exists in PostgreSQL first, then run:

```bash
python sql/create_table.py
```

You should see:
```
Schema and table created successfully.
```

---

## Running the Pipeline Manually

```bash
python python/pipeline.py
```

The pipeline scrapes and saves in batches of 20 books at a time:

```
Starting ETL Pipeline...
Found 50 categories

--- Batch 1 (20 books scraped) ---
    Cleaned: 20 records
    Saved to DB. Running total: 20 books

--- Batch 2 (20 books scraped) ---
    Cleaned: 20 records
    Saved to DB. Running total: 40 books
```

**For a quick test run** (~40 books), open `pipeline.py` and change:
```python
extract_books_batched(batch_size=20, max_pages=2)
```

**To stop the pipeline at any time:** `Ctrl + C`

---

## Automated Scheduling (Windows Task Scheduler)

The `run_pipeline.bat` file automates the pipeline on a schedule without
any manual intervention. Each run is logged to `data/logs/scheduler.log`.

### Step 1 — Test the batch file manually first

Double-click `run_pipeline.bat` or run from terminal:

```bash
run_pipeline.bat
```

Confirm it completes and check `data/logs/scheduler.log` shows:
```
[DD/MM/YYYY HH:MM:SS] Pipeline starting...
[DD/MM/YYYY HH:MM:SS] Pipeline completed successfully.
```

### Step 2 — Open Windows Task Scheduler

Press `Win + S` and search for **Task Scheduler**, then open it.

### Step 3 — Create a new task

Click **Create Basic Task** in the right panel and follow these steps:

| Field | Value |
|-------|-------|
| Name | `Books Pipeline` |
| Description | `Daily ETL run for books price intelligence` |
| Trigger | Daily |
| Start time | `06:00:00` (or any time you prefer) |
| Action | Start a program |
| Program/script | Browse to your `run_pipeline.bat` file |
| Start in | Your project root e.g. `C:\DE2026\ShopEasy-Scraper-ETL-Pipeline` |

### Step 4 — Confirm the task

Click **Finish**. Your pipeline will now run automatically every day at the
time you set. To verify, find **Books Pipeline** in the Task Scheduler library
and check the **Next Run Time** column.

### Step 5 — Check the logs after a scheduled run

```bash
type data\logs\scheduler.log
```

You will see a timestamped entry for every run:
```
[10/05/2026 06:00:01] Pipeline starting...
[10/05/2026 06:04:22] Pipeline completed successfully.
[11/05/2026 06:00:01] Pipeline starting...
[11/05/2026 06:04:19] Pipeline completed successfully.
```

---

## Re-running the Pipeline (Idempotency)

The pipeline is safe to re-run. It will not create duplicate records.

- `ON CONFLICT (product_id, source) DO NOTHING` in `load.py` skips any book already in the database
- `drop_duplicates()` in `transform.py` removes duplicates within each batch

To also **update** existing records with fresh prices on each run:

```python
# In load.py, change DO NOTHING to DO UPDATE:
ON CONFLICT (product_id, source) DO UPDATE SET
    price      = EXCLUDED.price,
    rating     = EXCLUDED.rating,
    in_stock   = EXCLUDED.in_stock,
    scraped_at = EXCLUDED.scraped_at
```

---

## Running the Analytics Queries

Once data has been loaded, run the full analytics script:

```bash
psql -U postgres -d shopeasy -f sql/analytics.sql
```

If you see an encoding error on Windows, run this first:

```bash
chcp 65001
psql -U postgres -d shopeasy -f sql/analytics.sql
```

### What the analytics script includes

| Query | Business Question |
|-------|-----------------|
| **1. Price Overview** | What are the most expensive books? |
| **2. Overpriced / Underpriced** | Which books are outliers vs their category average? |
| **3. Category Price Variation** | Which categories have the most inconsistent pricing? |
| **4. Best Value Books** | Which books have the highest rating relative to price? |
| **5. Avg Price per Rating** | Do higher rated books cost more? |
| **6. Out of Stock by Category** | Which categories have supply issues? |
| **7. Pipeline Summary** | Total books loaded, avg price, cheapest and most expensive |

To run a single query, open pgAdmin, paste it into the Query Tool and press **F5**.

---

## Database Schema

```
Database : shopeasy
Schema   : books
Table    : books.books
```

```sql
CREATE TABLE books.books (
    product_id   VARCHAR      NOT NULL,
    product_name VARCHAR      NOT NULL,
    category     VARCHAR,
    price        FLOAT,
    rating       SMALLINT,
    in_stock     BOOLEAN DEFAULT TRUE,
    source       VARCHAR      NOT NULL,
    scraped_at   TIMESTAMPTZ  DEFAULT NOW(),

    PRIMARY KEY (product_id, source)
);
```

---

## How It Works

### Extract — `extract_books.py`
- Checks `robots.txt` before starting
- Discovers all 50 categories from the homepage sidebar
- Paginates through every listing page
- Visits each book's detail page to collect full data
- Yields batches as it goes rather than waiting until the end
- Waits `SCRAPE_DELAY` seconds between requests

### Transform — `transform.py`
- Strips `£` symbols from prices and casts to float
- Converts word-based ratings (`"Three"`) to integers (`3`)
- Converts availability strings to `True`/`False`
- Drops rows with unparseable prices
- Removes duplicates within each batch

### Load — `load.py`
- Inserts each batch into `books.books` immediately after transformation
- Uses `ON CONFLICT DO NOTHING` so re-running won't create duplicates

---

## Logs

| File | Contents |
|------|----------|
| `data/logs/app.log` | Detailed pipeline activity — scraping progress, errors, record counts |
| `data/logs/scheduler.log` | One entry per scheduled run — timestamp and success or failure |

---

## Requirements

```
selenium
beautifulsoup4
requests
pandas
webdriver-manager
python-dotenv
sqlalchemy
psycopg2-binary
```

---

## Notes

- The `.env` file should be added to `.gitignore` — never commit credentials
- `books.toscrape.com` is built specifically for scraping practice — no real data, no restrictions in `robots.txt`
- The price change over time query (Query 4 in analytics) becomes meaningful after the pipeline has run on at least two separate days