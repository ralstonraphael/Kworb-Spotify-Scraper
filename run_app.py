"""
Entry point for the Kworb Spotify Scraper application.
Run this file from the project root directory.
"""
import streamlit.web.bootstrap
from src.ui.streamlit_app import main

if __name__ == "__main__":
    streamlit.web.bootstrap.run("src/ui/streamlit_app.py", "", [], []) 