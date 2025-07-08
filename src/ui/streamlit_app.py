"""Streamlit app for Spotify chart data visualization."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import ChartScraper
from ai_helper import AIHelper

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="Spotify Chart Analyzer",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 Spotify Chart Analyzer")
    
    st.markdown("""
    This app helps you analyze Spotify chart data and track performance over time.
    Enter a Spotify track URL to get started!
    """)
    
    # Initialize AI helper with error handling
    try:
        ai_helper = AIHelper()
    except ValueError as e:
        st.error(f"Error initializing AI helper: {str(e)}")
        st.warning("Please configure your OpenAI API key in the app settings.")
        return
    except Exception as e:
        st.error(f"Unexpected error initializing AI helper: {str(e)}")
        return
    
    # Initialize scraper
    try:
        scraper = ChartScraper(use_selenium=True)
    except Exception as e:
        st.error(f"Error initializing scraper: {str(e)}")
        return
    
    # Track URL input
    st.sidebar.subheader("🎵 Track History")
    track_url = st.sidebar.text_input(
        "Enter Spotify Track URL",
        placeholder="https://open.spotify.com/track/..."
    )
    
    if track_url:
        try:
            # Extract track ID from URL
            track_id = track_url.split("/")[-1].split("?")[0]
            
            # Scrape track history
            with st.spinner("Fetching track data..."):
                df = scraper.scrape_track_history(track_id)
            
            if df is not None and not df.empty:
                # Display the data
                st.subheader("📊 Track Performance Data")
                st.dataframe(df)
                
                # Process data with AI
                try:
                    with st.spinner("Analyzing data with AI..."):
                        insights = ai_helper.analyze_track_data(df.to_dict("records"))
                    
                    st.subheader("🤖 AI Insights")
                    st.write(insights)
                except Exception as e:
                    st.error(f"Error analyzing data with AI: {str(e)}")
            else:
                st.warning("No data found for this track.")
        except Exception as e:
            st.error(f"Error processing track: {str(e)}")

if __name__ == "__main__":
    main() 