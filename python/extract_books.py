import time
import hashlib
import requests
from bs4 import BeautifulSoup
from logger import logger
from config import BASE_URL, SCRAPE_DELAY
from urllib.parse import urljoin

# Politely identify our bot to the server
HEADERS = {"User-Agent": "BooksScraperBot/1.0 (educational project)"}

# Maps the written star-rating on the site to a number
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def get_page(url):
    """
    Fetch a single URL and return a BeautifulSoup object.
    Retries up to 3 times if the request fails.
    Returns None if all attempts fail.
    """
    for attempt in range(1, 4):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt} failed for {url} — {e}")
            time.sleep(attempt * 2)  # wait a bit longer after each failure
    logger.error(f"Could not fetch {url} after 3 attempts")
    return None


def get_categories(soup):
    """
    Read the homepage sidebar and return a dict of
    {category_name: category_url} for every category on the site.
    """
    categories = {}
    for link in soup.select("ul.nav-list > li > ul > li > a"):
        name = link.get_text(strip=True)
        url  = BASE_URL + "/" + link["href"].strip()
        categories[name] = url
    return categories


def scrape_detail_page(url, category):
    """
    Visit one book's detail page and pull all the fields we need.
    Returns a dict, or None if the page couldn't be parsed.
    """
    soup = get_page(url)
    if not soup:
        return None

    try:
        # The product info table holds UPC, price, availability etc.
        table = {
            row.th.get_text(strip=True): row.td.get_text(strip=True)
            for row in soup.select("table.table-striped tr")
            if row.th and row.td          # only process rows that have both cells
        }

        title       = soup.select_one("h1").get_text(strip=True)
        price_raw   = soup.select_one("p.price_color").get_text(strip=True)
        rating_word = soup.select_one("p.star-rating")["class"][1]  # e.g. "Three"
        upc         = table.get("UPC", "")

        # Use UPC as the unique product ID — same approach as your hashlib id
        product_id = hashlib.md5((upc + category).encode()).hexdigest()

        return {
            "product_id":   product_id,
            "product_name": title,
            "category":     category,
            "price":        price_raw,          # cleaned later in transform
            "rating":       rating_word,        # converted to int in transform
            "in_stock":     table.get("Availability", ""),
            "upc":          upc,
            "source":       "BooksToScrape"
        }

    except Exception as e:
        logger.warning(f"Error parsing detail page {url} — {e}")
        return None


def extract_books(max_pages=0):
    """
    Main extraction function — mirrors extract_jumia() from your original code.

    Crawls the entire books.toscrape.com site:
      1. Reads all categories from the homepage sidebar
      2. Paginates through each category's listing pages
      3. Visits each book's detail page to get full data

    max_pages=0 means scrape everything (~50 pages, ~1000 books).
    Set max_pages=2 for a quick test run (~40 books).
    """
    logger.info("Starting Books extraction")

    # Check robots.txt first — good practice before any scraping
    robots = requests.get(BASE_URL + "/robots.txt", headers=HEADERS, timeout=10)
    logger.info(f"robots.txt status: {robots.status_code}")

    homepage = get_page(BASE_URL)
    if not homepage:
        logger.error("Could not load homepage — aborting")
        return []

    categories = get_categories(homepage)
    logger.info(f"Found {len(categories)} categories")

    data = []
    pages_scraped = 0

    for category_name, category_url in categories.items():
        current_url = category_url

        while current_url:
            # Honour the max_pages limit (0 = no limit)
            if max_pages and pages_scraped >= max_pages:
                logger.info(f"Reached max_pages={max_pages} — stopping early")
                return data

            logger.info(f"Scraping: {current_url}")
            soup = get_page(current_url)
            if not soup:
                break

            pages_scraped += 1

            # Each article on the listing page links to a detail page
            for article in soup.select("article.product_pod"):
                relative_href = article.select_one("h3 > a")["href"]
                detail_url = urljoin(current_url, relative_href)

                time.sleep(SCRAPE_DELAY)  # be polite — pause between requests
                book = scrape_detail_page(detail_url, category_name)
                if book:
                    data.append(book)

            # Follow the "next" pagination button if there is one
            next_btn    = soup.select_one("li.next > a")
            current_url = urljoin(current_url, next_btn["href"]) if next_btn else None

    logger.info(f"Extracted {len(data)} books from BooksToScrape")
    return data

def extract_books_batched(batch_size=20, max_pages=0):
    """
    Same crawl logic as extract_books() but yields a batch of books
    every `batch_size` records instead of waiting until the end.
    This lets the pipeline save to the database as it goes.
    """
    logger.info("Starting batched extraction")

    robots = requests.get(BASE_URL + "/robots.txt", headers=HEADERS, timeout=10)
    logger.info(f"robots.txt status: {robots.status_code}")

    homepage = get_page(BASE_URL)
    if not homepage:
        logger.error("Could not load homepage — aborting")
        return

    categories = get_categories(homepage)
    logger.info(f"Found {len(categories)} categories")

    batch = []
    pages_scraped = 0

    for category_name, category_url in categories.items():
        current_url = category_url

        while current_url:
            if max_pages and pages_scraped >= max_pages:
                # Yield whatever is left in the final partial batch
                if batch:
                    yield batch
                return

            logger.info(f"Scraping: {current_url}")
            soup = get_page(current_url)
            if not soup:
                break

            pages_scraped += 1

            for article in soup.select("article.product_pod"):
                anchor = article.select_one("h3 > a")
                if not anchor:
                    continue
                detail_url = urljoin(current_url, anchor["href"])

                time.sleep(SCRAPE_DELAY)
                book = scrape_detail_page(detail_url, category_name)
                if book:
                    batch.append(book)

                # Once the batch is full, yield it and start a new one
                if len(batch) >= batch_size:
                    yield batch
                    batch = []   # reset for the next batch

            next_btn    = soup.select_one("li.next > a")
            current_url = urljoin(current_url, next_btn["href"]) if next_btn else None

    # Yield any remaining books that didn't fill a complete batch
    if batch:
        yield batch