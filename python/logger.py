import logging
import os

# Create the logs folder if it doesn't exist yet
os.makedirs("data/logs", exist_ok=True)

logging.basicConfig(
    filename="data/logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Also print logs to the terminal so you can see progress while it runs
logging.getLogger().addHandler(logging.StreamHandler())

logger = logging.getLogger()
