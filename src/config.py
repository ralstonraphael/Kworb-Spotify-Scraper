"""Configuration settings for the application."""

# Scraper settings
KWORB_BASE_URL = "https://kworb.net/spotify"
WAIT_TIME = 15  # seconds - increased for slower connections
RETRY_COUNT = 5  # increased number of retries

# Streamlit settings
STREAMLIT_PAGE_TITLE = "Spotify Chart Analyzer"
STREAMLIT_PAGE_ICON = "🎵"

# Data directories
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed" 