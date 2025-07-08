"""Streamlit UI for the Spotify Chart Scraper application."""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs
import os

import pandas as pd
import streamlit as st
import altair as alt
from tqdm import tqdm
from dotenv import load_dotenv

# Use relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src import config
from src.cleaner import DataCleaner
from src.scraper import ChartScraper, ScrapingError
from src.ai_helper import AIHelper

# Configure logging
logging.basicConfig(
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get OpenAI API key from Streamlit secrets or environment variable
def get_openai_api_key():
    """Get OpenAI API key from Streamlit secrets or environment variable."""
    try:
        return st.secrets["OPENAI_API_KEY"]
    except:
        # Fallback to environment variable
        load_dotenv()
        return os.getenv("OPENAI_API_KEY")

# Initialize helpers
ai_helper = AIHelper()

# Set page config for a clean look
st.set_page_config(
    page_title=config.STREAMLIT_PAGE_TITLE,
    page_icon=config.STREAMLIT_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

def extract_track_id(url: str) -> Optional[str]:
    """Extract track ID from Spotify or KWORB URL."""
    try:
        # Handle Spotify URLs
        if 'open.spotify.com' in url:
            return url.split('/')[-1].split('?')[0]
        # Handle KWORB URLs
        elif 'kworb.net/spotify/track' in url:
            return url.split('/')[-1].replace('.html', '')
        # Handle raw track IDs
        elif re.match(r'^[a-zA-Z0-9]{22}$', url):
            return url
        return None
    except Exception:
        return None

def display_track_history(df: pd.DataFrame, track_id: str):
    """Display track streaming history."""
    st.subheader("🎵 Track Streaming History")
    
    # Display summary metrics from Total row
    if 'Total' in df['date'].values:
        total_row = df[df['date'] == 'Total'].iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Global Streams", f"{total_row['Global']:,}")
        with col2:
            st.metric("Total US Streams", f"{total_row['US']:,}")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📊 Chart", "📋 Data"])
    
    with tab1:
        # Chart visualization
        if not df.empty:
            # Filter out Total and Peak rows for the chart
            chart_df = df[~df['date'].isin(['Total', 'Peak'])]
            
            # Create line chart for Global and US streams
            chart_data = pd.melt(
                chart_df,
                id_vars=['date'],
                value_vars=['Global', 'US'],
                var_name='Region',
                value_name='Streams'
            )
            
            chart = alt.Chart(chart_data).mark_line().encode(
                x=alt.X('date:T', title='Date'),
                y=alt.Y('Streams:Q', title='Streams'),
                color='Region:N',
                tooltip=['date:T', 'Region:N', 'Streams:Q']
            ).properties(height=400)
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No streaming history data available.")
    
    with tab2:
        # Display full data table
        if not df.empty:
            # Format numbers with commas
            st.dataframe(
                df.style.format({
                    'Global': '{:,.0f}',
                    'US': '{:,.0f}'
                }, na_rep="--"),
                hide_index=True
            )
        else:
            st.info("No data available to display.")
    
    # Add download button if we have data
    if not df.empty:
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"track_{track_id}_history.csv",
            "text/csv",
            key=f"download_{track_id}"
        )

def main():
    """Main Streamlit application."""
    st.title("🎵 Spotify Chart History Scraper")
    st.markdown("""
    Extract and analyze historical Spotify chart data from KWORB.net.
    Enter a track URL or ID in the sidebar to begin.
    """)
    
    # Initialize scraper
    scraper = ChartScraper(use_selenium=True)
    
    # Track URL input
    st.sidebar.subheader("🎵 Track History")
    track_url = st.sidebar.text_input(
        "Enter Spotify Track URL or ID",
        help="Enter a Spotify track URL or KWORB track URL"
    )
    
    if track_url:
        track_id = extract_track_id(track_url)
        if not track_id:
            st.sidebar.error("Invalid track URL or ID")
        else:
            try:
                with st.spinner("Fetching track history..."):
                    df = scraper.scrape_track_history(track_id)
                    display_track_history(df, track_id)
            except Exception as e:
                st.error(f"Failed to fetch track history: {str(e)}")
                return

if __name__ == "__main__":
    main() 