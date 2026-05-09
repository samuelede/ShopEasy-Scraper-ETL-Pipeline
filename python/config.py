import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host":     os.getenv("DB_HOST"),
    "port":     os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME")
}

# Scraper settings — edit these to control how the scraper behaves
SCRAPE_DELAY = float(os.getenv("SCRAPE_DELAY", 1.5))  # seconds between requests
BASE_URL     = "https://books.toscrape.com"
