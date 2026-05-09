import re
import pandas as pd
from logger import logger

# Maps the written star-rating on the site to a number
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def clean_price(price):
    """
    Strips currency symbols and converts to float.
    '£12.99' → 12.99    'Â£51.77' → 51.77    'N/A' → None

    Keeps your original clean_data() logic but handles the £ encoding
    issue that books.toscrape.com sometimes has.
    """
    if not price:
        return None

    if isinstance(price, (int, float)):
        return price

    try:
        # Remove everything except digits and the decimal point
        return float(re.sub(r"[^\d.]", "", str(price)))
    except ValueError:
        return None


def clean_rating(rating):
    """
    Converts the word rating from the site to an integer.
    'Three' → 3    'Five' → 5    anything else → None
    """
    if isinstance(rating, (int, float)):
        try:
            return int(rating)
        except:
            return None

    # Try the word map first (books.toscrape uses words like "Three")
    if isinstance(rating, str):
        mapped = RATING_MAP.get(rating.strip().capitalize())
        if mapped:
            return mapped
        # Fall back to parsing as a number
        try:
            return int(float(rating.strip()))
        except:
            return None

    return None


def clean_availability(raw):
    """Convert the availability string to a simple True/False."""
    if not raw:
        return True  # default to in stock if unknown
    return "in stock" in str(raw).lower()


def transform_data(raw_data):
    """
    Cleans and type-casts the raw scraped data.
    Mirrors your original transform_data() — same structure, updated for books fields.

    Returns a pandas DataFrame ready to pass to load_data().
    """
    # Guard: return empty DataFrame if nothing was scraped
    if not raw_data:
        logger.warning("No data passed to transform_data! Returning an empty DataFrame.")
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)

    # Guard: check the expected columns exist before transforming
    if "price" not in df.columns:
        logger.error(f"Missing 'price' column! Columns found: {df.columns.tolist()}")
        df["price"] = None

    # Clean price — strip £ symbol, cast to float
    df["price"] = df["price"].apply(clean_price)

    # Convert rating word to integer
    df["rating"] = df["rating"].apply(clean_rating)

    # Convert availability string to boolean
    if "in_stock" in df.columns:
        df["in_stock"] = df["in_stock"].apply(clean_availability)

    # Drop rows where price couldn't be parsed — they'd break the DB insert
    before = len(df)
    df = df.dropna(subset=["price"])
    dropped = before - len(df)
    if dropped:
        logger.warning(f"Dropped {dropped} rows with unparseable prices")

    # Remove duplicates within this batch based on product_id
    df = df.drop_duplicates(subset=["product_id"])

    logger.info(f"Transform complete — {len(df)} clean records")
    return df
