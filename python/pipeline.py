from extract_books import extract_books_batched
from transform import transform_data
from load import load_data
from logger import logger


def run_pipeline():
    print("Starting ETL Pipeline...")
    total_loaded = 0

    # Process and save every 20 books as they are scraped
    for batch_num, raw_batch in enumerate(extract_books_batched(batch_size=20), start=1):
        print(f"\n--- Batch {batch_num} ({len(raw_batch)} books scraped) ---")

        # Transform this batch
        clean_df = transform_data(raw_batch)
        print(f"    Cleaned: {len(clean_df)} records")

        # Load this batch into the database immediately
        load_data(clean_df)
        total_loaded += len(clean_df)
        print(f"    Saved to DB. Running total: {total_loaded} books")

    print(f"\nPipeline complete — {total_loaded} books loaded in total.")


if __name__ == "__main__":
    run_pipeline()