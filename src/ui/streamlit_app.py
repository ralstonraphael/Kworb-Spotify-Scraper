"""Streamlit app for Spotify chart data visualization."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import project modules using absolute imports
from src.ai_helper import AIHelper
from src.scraper import ChartScraper
from src.cleaner import DataCleaner
import src.config as config

def extract_track_id(url: str) -> str:
    """Extract track ID from Spotify URL."""
    if not url:
        return ""
    
    # Clean the input
    url = url.strip()
    
    # Handle different Spotify URL formats
    if "spotify.com/track/" in url:
        # Extract ID from full URL
        track_id = url.split("track/")[-1].split("?")[0].split("/")[0]
    elif "spotify:track:" in url:
        # Extract ID from URI
        track_id = url.split("spotify:track:")[-1].split("?")[0]
    elif "kworb.net/spotify/track/" in url:
        # Extract ID from Kworb URL
        track_id = url.split("track/")[-1].split(".")[0]
    else:
        # Assume it's just the ID
        track_id = url.split("?")[0].strip()
    
    # Clean the track ID
    track_id = track_id.strip()
    
    # Validate track ID format (should be a string of alphanumeric characters)
    if not track_id.replace("-", "").isalnum():
        st.error("❌ Invalid track ID format. Please provide a valid Spotify track URL or ID.")
        return ""
    
    return track_id

def main():
    """Main function to run the Streamlit app."""
    # Set up page config
    st.set_page_config(
        page_title=config.STREAMLIT_PAGE_TITLE,
        page_icon=config.STREAMLIT_PAGE_ICON,
        layout="wide"
    )

    st.title("🎵 Spotify Chart Analyzer")

    st.markdown("""
    This app helps you analyze Spotify chart data and track performance over time.
    Enter a Spotify track URL to get started!
    
    **Supported URL formats:**
    - Full URL: `https://open.spotify.com/track/...`
    - Spotify URI: `spotify:track:...`
    - Track ID: Just paste the ID
    """)

    # API Key handling in sidebar
    st.sidebar.title("⚙️ Settings")
    api_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys",
        placeholder="sk-..."
    )

    if not api_key:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar to enable AI analysis.")
        st.info("Don't have an API key? Get one at [OpenAI's website](https://platform.openai.com/api-keys)")
        return

    # Initialize AI helper with error handling
    try:
        ai_helper = AIHelper(api_key=api_key)
    except ValueError as e:
        st.error(f"Error initializing AI helper: {str(e)}")
        st.warning("Please check your OpenAI API key and try again.")
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
            track_id = extract_track_id(track_url)
            
            if not track_id:
                return
            
            st.info(f"🔍 Analyzing track: {track_id}")
            
            # Scrape track history
            with st.spinner("Fetching track data..."):
                df = scraper.scrape_track_history(track_id)

            if df is not None and not df.empty:
                # Display track info
                song_name = df['song_name'].iloc[0]
                artist_name = df['artist_name'].iloc[0]
                
                st.subheader("🎵 Track Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Song:** {song_name}")
                with col2:
                    st.markdown(f"**Artist:** {artist_name}")
                
                # Display the data
                st.subheader("📊 Track Performance")
                
                # Create metrics for Total streams
                if 'Total' in df['date'].values:
                    total_row = df[df['date'] == 'Total'].iloc[0]
                    peak_row = df[df['date'] == 'Peak'].iloc[0] if 'Peak' in df['date'].values else None
                    
                    # Display metrics in columns
                    metric_cols = st.columns(4)
                    
                    # Global streams
                    with metric_cols[0]:
                        st.metric(
                            "Global Streams",
                            f"{total_row['Global']:,.0f}",
                            f"Peak: {peak_row['Global']:,.0f}" if peak_row is not None else None
                        )
                    
                    # US streams
                    if 'US' in df.columns:
                        with metric_cols[1]:
                            st.metric(
                                "US Streams",
                                f"{total_row['US']:,.0f}",
                                f"Peak: {peak_row['US']:,.0f}" if peak_row is not None else None
                            )
                    
                    # UK streams
                    if 'GB' in df.columns:
                        with metric_cols[2]:
                            st.metric(
                                "UK Streams",
                                f"{total_row['GB']:,.0f}",
                                f"Peak: {peak_row['GB']:,.0f}" if peak_row is not None else None
                            )
                    
                    # Other top market
                    other_markets = [col for col in df.columns if col not in ['date', 'song_name', 'artist_name', 'Global', 'US', 'GB']]
                    if other_markets:
                        top_market = max(other_markets, key=lambda x: total_row[x])
                        with metric_cols[3]:
                            st.metric(
                                f"Top Market ({top_market})",
                                f"{total_row[top_market]:,.0f}",
                                f"Peak: {peak_row[top_market]:,.0f}" if peak_row is not None else None
                            )
                
                # Process data with AI first
                try:
                    with st.spinner("Analyzing data..."):
                        insights = ai_helper.analyze_track_data(df.to_dict("records"))

                    st.subheader("🤖 Key Insights")
                    st.write(insights)
                except Exception as e:
                    st.error(f"Error analyzing data with AI: {str(e)}")
                    if "Rate limit" in str(e):
                        st.warning("OpenAI API rate limit reached. Please wait a few minutes and try again.")
                    elif "Incorrect API key" in str(e):
                        st.warning("Invalid API key. Please check your OpenAI API key in the sidebar.")
                
                # Create line chart for streaming history
                st.subheader("📈 Streaming History")
                
                # Filter out Total and Peak rows and sort by date
                chart_df = df[~df['date'].isin(['Total', 'Peak'])].copy()
                chart_df['date'] = pd.to_datetime(chart_df['date'])
                chart_df = chart_df.sort_values('date')
                
                # Create the line chart focusing on Global streams
                chart_data = pd.DataFrame({
                    'Date': chart_df['date'],
                    'Global Streams': chart_df['Global']
                })
                
                # Create and display the chart
                st.line_chart(
                    chart_data.set_index('Date'),
                    height=400,
                    use_container_width=True
                )
                
                # Display the full data table in an expander
                with st.expander("📋 View Full Data"):
                    st.dataframe(df, height=300)
                
            else:
                st.error("❌ No data found for this track. This could be because:")
                st.markdown("""
                - The track ID is invalid
                - The track is not available on Spotify
                - The website is blocking our requests
                - The website's structure has changed
                
                Please check the track URL and try again.
                """)
        except Exception as e:
            st.error(f"Error processing track: {str(e)}")

if __name__ == "__main__":
    main() 