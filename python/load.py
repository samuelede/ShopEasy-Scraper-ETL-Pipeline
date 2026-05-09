from sqlalchemy import create_engine, text
from config import DB_CONFIG
from logger import logger


def get_engine():
    """Build and return a SQLAlchemy engine from the DB_CONFIG settings."""
    return create_engine(
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )


def load_data(books_df):
    """
    Load the cleaned DataFrame into PostgreSQL.
    Mirrors your original load_data() — same structure, updated for books table.

    Uses ON CONFLICT DO NOTHING so re-running the pipeline won't create duplicates.
    The books table uses (product_id, source) as its unique key, same as your original.
    """
    if books_df.empty:
        logger.warning("Nothing to load — DataFrame is empty")
        return

    engine = get_engine()

    with engine.begin() as conn:
        for _, row in books_df.iterrows():
            conn.execute(text("""
                INSERT INTO books.books
                    (product_id, product_name, category, price, rating, in_stock, source)
                VALUES
                    (:product_id, :product_name, :category, :price, :rating, :in_stock, :source)
                ON CONFLICT (product_id, source) DO NOTHING
            """), {
                "product_id":   row["product_id"],
                "product_name": row["product_name"],
                "category":     row["category"],
                "price":        row["price"],
                "rating":       row.get("rating"),
                "in_stock":     row.get("in_stock", True),
                "source":       row["source"],
            })

    logger.info(f"Loaded {len(books_df)} records into the database")
