"""Configuration settings for the application."""

# Scraper settings
KWORB_BASE_URL = "https://kworb.net/spotify"
WAIT_TIME = 10  # seconds
RETRY_COUNT = 3

# Streamlit settings
STREAMLIT_PAGE_TITLE = "Spotify Chart Analyzer"
STREAMLIT_PAGE_ICON = "🎵"

# Data directories
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed" 