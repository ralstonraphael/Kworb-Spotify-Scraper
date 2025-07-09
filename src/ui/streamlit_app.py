"""Streamlit app for Spotify chart data visualization."""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os
import gc
import tracemalloc
import psutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_memory_usage():
    """Log current memory usage."""
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / 1024 / 1024  # Convert to MB
    logger.info(f"Memory usage: {mem:.2f} MB")

# Start memory tracking
tracemalloc.start()

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

def apply_custom_css():
    """Apply custom CSS for Apple-style design."""
    st.markdown("""
        <style>
        /* Main container */
        .main {
            padding: 2rem;
        }
        
        /* Headers */
        h1 {
            font-weight: 700 !important;
            letter-spacing: -0.025em !important;
        }
        
        h2 {
            font-weight: 600 !important;
            letter-spacing: -0.025em !important;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-weight: 600 !important;
        }
        
        /* Cards */
        [data-testid="stExpander"] {
            background-color: #F5F5F7 !important;
            border-radius: 10px !important;
            border: none !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }
        
        /* Buttons */
        .stButton button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #F5F5F7 !important;
        }
        
        /* Input fields */
        .stTextInput input {
            border-radius: 8px !important;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    """Main function to run the Streamlit app."""
    # Log initial memory usage
    log_memory_usage()
    
    # Force garbage collection
    gc.collect()
    
    # Set up page config
    st.set_page_config(
        page_title=config.STREAMLIT_PAGE_TITLE,
        page_icon=config.STREAMLIT_PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    apply_custom_css()

    # Log memory after setup
    log_memory_usage()

    # Create a clean header with logo and title
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/168px-Spotify_logo_without_text.svg.png", width=100)
    with col2:
        st.title("Spotify Chart Analyzer")
        st.markdown("""
        Analyze Spotify chart data and track performance with AI-powered insights.
        Get detailed streaming metrics and performance analysis for any track.
        """)

    # Settings in sidebar with modern styling
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.markdown("---")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key to enable AI analysis",
            placeholder="sk-..."
        )

        if not api_key:
            st.warning("⚠️ Enter your OpenAI API key to enable AI analysis")
            st.markdown("""
            <a href="https://platform.openai.com/api-keys" target="_blank" 
               style="text-decoration: none; color: #007AFF; font-weight: 500;">
                Get an API key →
            </a>
            """, unsafe_allow_html=True)
            return

    try:
        # Initialize components with proper cleanup
        if 'ai_helper' not in st.session_state:
            st.session_state.ai_helper = AIHelper(api_key=api_key)
        if 'scraper' not in st.session_state:
            st.session_state.scraper = ChartScraper(use_selenium=True)
            
        # Log memory after initialization
        log_memory_usage()
        
        # Initialize scraper
        try:
            scraper = st.session_state.scraper
        except Exception as e:
            st.error(f"Error initializing scraper: {str(e)}")
            return

        # Modern search bar
        st.markdown("### 🔍 Track Search")
        track_url = st.text_input(
            "",
            placeholder="Enter Spotify track URL or ID...",
            help="Paste a Spotify track URL, URI, or ID to analyze its performance"
        )

        # Display supported formats in a clean way
        with st.expander("ℹ️ Supported URL formats"):
            st.markdown("""
            - **Spotify URL**: `https://open.spotify.com/track/...`
            - **Spotify URI**: `spotify:track:...`
            - **Track ID**: Just the ID string
            """)

        if track_url:
            try:
                # Extract track ID from URL
                track_id = extract_track_id(track_url)
                
                if not track_id:
                    return
                
                # Create a progress container
                progress_container = st.empty()
                with progress_container.container():
                    st.info("🔍 Analyzing track data...")
                    progress_bar = st.progress(0)
                
                # Scrape track history
                df = scraper.scrape_track_history(track_id)
                progress_bar.progress(50)

                if df is not None and not df.empty:
                    # Update progress
                    progress_bar.progress(75)
                    
                    # Clear progress container
                    progress_container.empty()
                    
                    # Display track info in a modern card
                    song_name = df['song_name'].iloc[0]
                    artist_name = df['artist_name'].iloc[0]
                    
                    st.markdown(f"""
                    <div style="background-color: #F5F5F7; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h2 style="margin: 0; color: #1D1D1F;">{song_name}</h2>
                        <p style="margin: 0.5rem 0 0 0; color: #6E6E73;">{artist_name}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Create modern metrics display
                    if 'Total' in df['date'].values:
                        total_row = df[df['date'] == 'Total'].iloc[0]
                        peak_row = df[df['date'] == 'Peak'].iloc[0] if 'Peak' in df['date'].values else None
                        
                        st.markdown("### 📊 Performance Metrics")
                        
                        # Create metric columns with modern styling
                        metrics_container = st.container()
                        with metrics_container:
                            cols = st.columns(4)
                            
                            # Global streams
                            with cols[0]:
                                st.metric(
                                    "Global Streams",
                                    f"{total_row['Global']:,.0f}",
                                    f"Peak: {peak_row['Global']:,.0f}" if peak_row is not None else None,
                                    delta_color="normal"
                                )
                            
                            # US streams
                            if 'US' in df.columns:
                                with cols[1]:
                                    st.metric(
                                        "US Streams",
                                        f"{total_row['US']:,.0f}",
                                        f"Peak: {peak_row['US']:,.0f}" if peak_row is not None else None,
                                        delta_color="normal"
                                    )
                            
                            # UK streams
                            if 'GB' in df.columns:
                                with cols[2]:
                                    st.metric(
                                        "UK Streams",
                                        f"{total_row['GB']:,.0f}",
                                        f"Peak: {peak_row['GB']:,.0f}" if peak_row is not None else None,
                                        delta_color="normal"
                                    )
                            
                            # Other top market
                            other_markets = [col for col in df.columns if col not in ['date', 'song_name', 'artist_name', 'Global', 'US', 'GB']]
                            if other_markets:
                                top_market = max(other_markets, key=lambda x: total_row[x])
                                with cols[3]:
                                    st.metric(
                                        f"Top Market ({top_market})",
                                        f"{total_row[top_market]:,.0f}",
                                        f"Peak: {peak_row[top_market]:,.0f}" if peak_row is not None else None,
                                        delta_color="normal"
                                    )
                    
                    # Update progress
                    progress_bar.progress(90)
                    
                    # Process data with AI
                    try:
                        with st.spinner("Generating AI insights..."):
                            insights = st.session_state.ai_helper.analyze_track_data(df.to_dict("records"))
                            
                            st.markdown("### 🤖 AI Insights")
                            st.markdown(f"""
                            <div style="background-color: #F5F5F7; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                                {insights}
                            </div>
                            """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error analyzing data with AI: {str(e)}")
                        if "Rate limit" in str(e):
                            st.warning("OpenAI API rate limit reached. Please wait a few minutes and try again.")
                        elif "Incorrect API key" in str(e):
                            st.warning("Invalid API key. Please check your OpenAI API key in the sidebar.")
                    
                    # Create modern streaming history chart
                    st.markdown("### 📈 Streaming History")
                    
                    # Filter out Total and Peak rows and sort by date
                    chart_df = df[~df['date'].isin(['Total', 'Peak'])].copy()
                    chart_df['date'] = pd.to_datetime(chart_df['date'])
                    chart_df = chart_df.sort_values('date')
                    
                    # Create the line chart focusing on Global streams
                    chart_data = pd.DataFrame({
                        'Date': chart_df['date'],
                        'Global Streams': chart_df['Global']
                    })
                    
                    # Create and display the chart with custom styling
                    st.line_chart(
                        chart_data.set_index('Date'),
                        height=400,
                        use_container_width=True
                    )
                    
                    # Display the full data table in a modern expander
                    with st.expander("📋 View Full Data"):
                        st.dataframe(
                            df.style.format({
                                col: "{:,.0f}" for col in df.columns 
                                if col not in ['date', 'song_name', 'artist_name']
                            }),
                            height=300,
                            use_container_width=True
                        )
                    
                    # Complete progress
                    progress_bar.progress(100)
                    
                else:
                    st.error("❌ No data found for this track")
                    st.markdown("""
                    <div style="background-color: #F5F5F7; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h3 style="margin: 0; color: #1D1D1F;">Possible reasons:</h3>
                        <ul style="margin: 0.5rem 0 0 0; color: #6E6E73;">
                            <li>Invalid track ID</li>
                            <li>Track not available on Spotify</li>
                            <li>Website blocking our requests</li>
                            <li>Website structure has changed</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error processing track: {str(e)}")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
    finally:
        # Cleanup
        gc.collect()
        log_memory_usage()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        st.error("The application encountered an error. Please refresh the page.") 