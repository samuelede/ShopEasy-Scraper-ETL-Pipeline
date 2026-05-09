"""
sql/create_table.py
--------------------
Creates the PostgreSQL schema and table for the books pipeline.
Run this ONCE before running pipeline.py for the first time.

Usage:
    python sql/create_table.py
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load .env from the project root (one level up from /sql)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "shopeasy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def create_tables():
    conn = get_connection()
    cur  = conn.cursor()

    # Create the shopeasy schema if it doesn't exist
    cur.execute("CREATE SCHEMA IF NOT EXISTS books;")

    # Main books table — matches the same (product_id, source) primary key
    # structure as your original gadgets table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books.shopeasy (
            product_id   VARCHAR     NOT NULL,
            product_name VARCHAR     NOT NULL,
            category     VARCHAR,
            price        FLOAT,
            rating       SMALLINT,        -- 1 to 5 stars
            in_stock     BOOLEAN DEFAULT TRUE,
            source       VARCHAR     NOT NULL,
            scraped_at   TIMESTAMPTZ DEFAULT NOW(),

            PRIMARY KEY (product_id, source)   -- same PK as your original table
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Schema and table created successfully.")


if __name__ == "__main__":
    create_tables()
