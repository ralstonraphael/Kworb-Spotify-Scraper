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

def basic_analysis(df, data_type="weekly"):
    """Provide basic statistical analysis without AI."""
    insights = []
    
    # Global performance
    if 'Global' in df.columns:
        total_streams = df[df['date'] == 'Total']['Global'].iloc[0]
        peak_streams = df[df['date'] == 'Peak']['Global'].iloc[0] if 'Peak' in df['date'].values else None
        insights.append(f"📈 Total Global Streams: {total_streams:,.0f}")
        if peak_streams:
            insights.append(f"🔝 Peak Global Streams: {peak_streams:,.0f}")
    
    # Market performance
    markets = [col for col in df.columns if col not in ['date', 'song_name', 'artist_name', 'Global']]
    if markets:
        total_row = df[df['date'] == 'Total'].iloc[0]
        top_market = max(markets, key=lambda x: total_row[x])
        insights.append(f"🌍 Best Performing Market: {top_market} with {total_row[top_market]:,.0f} streams")
    
    # Growth analysis
    chart_df = df[~df['date'].isin(['Total', 'Peak'])].copy()
    if not chart_df.empty:
        chart_df['date'] = pd.to_datetime(chart_df['date'])
        chart_df = chart_df.sort_values('date')
        
        if len(chart_df) > 1:
            first_streams = chart_df.iloc[0]['Global']
            last_streams = chart_df.iloc[-1]['Global']
            growth = ((last_streams - first_streams) / first_streams) * 100
            trend = "📈 growing" if growth > 0 else "📉 declining"
            
            # Add time-specific insights
            if data_type == "daily":
                days = (chart_df.iloc[-1]['date'] - chart_df.iloc[0]['date']).days
                avg_daily = chart_df['Global'].mean()
                insights.append(f"📊 Daily average: {avg_daily:,.0f} streams")
                insights.append(f"📅 Data spans {days} days")
            else:  # weekly
                weeks = len(chart_df)
                avg_weekly = chart_df['Global'].mean()
                insights.append(f"📊 Weekly average: {avg_weekly:,.0f} streams")
                insights.append(f"📅 Data spans {weeks} weeks")
            
            insights.append(f"📈 The track is {trend} with {abs(growth):.1f}% change over the tracked period")
    
    return "\n\n".join(insights)

def main():
    """Main function to run the Streamlit app."""
    # Set up page config
    st.set_page_config(
        page_title=config.STREAMLIT_PAGE_TITLE,
        page_icon=config.STREAMLIT_PAGE_ICON,
        layout="wide"
    )

    st.title("🎵 Spotify Chart Analyzer")

    # Sidebar navigation
    st.sidebar.title("⚙️ Settings")
    
    # Add data source selector
    data_source = st.sidebar.radio(
        "Data Source",
        ["Track History", "Country Charts"],
        help="Choose whether to analyze a specific track or country charts"
    )
    
    # Add data type selector
    data_type = st.sidebar.radio(
        "Data Type",
        ["Daily", "Weekly"],
        help="Choose whether to fetch daily or weekly data"
    ).lower()
    
    # AI Analysis toggle
    enable_ai = st.sidebar.checkbox(
        "Enable AI Analysis",
        value=False,
        help="Toggle to enable/disable AI-powered insights (requires OpenAI API key)"
    )
    
    api_key = None
    if enable_ai:
        api_key = st.sidebar.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys",
            placeholder="sk-..."
        )
        
        if not api_key:
            st.sidebar.warning("⚠️ Please enter your OpenAI API key to enable AI analysis.")
            st.sidebar.info("Don't have an API key? Get one at [OpenAI's website](https://platform.openai.com/api-keys)")

    # Initialize AI helper if enabled
    ai_helper = None
    if enable_ai and api_key:
        try:
            ai_helper = AIHelper(api_key=api_key)
        except ValueError as e:
            st.error(f"Error initializing AI helper: {str(e)}")
            st.warning("Please check your OpenAI API key and try again.")
        except Exception as e:
            st.error(f"Unexpected error initializing AI helper: {str(e)}")

    # Initialize scraper
    try:
        scraper = ChartScraper(use_selenium=True)
    except Exception as e:
        st.error(f"Error initializing scraper: {str(e)}")
        return

    if data_source == "Track History":
        st.markdown("""
        Enter a Spotify track URL to analyze its streaming history.
        
        **Supported URL formats:**
        - Full URL: `https://open.spotify.com/track/...`
        - Spotify URI: `spotify:track:...`
        - Track ID: Just paste the ID
        """)
        
        # Track URL input
        track_url = st.text_input(
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
                with st.spinner(f"Fetching {data_type} track data..."):
                    df = scraper.scrape_track_history(track_id, data_type=data_type)

                if df is not None and not df.empty:
                    # Display track info
                    song_name = df['song_name'].iloc[0]
                    artist_name = df['artist_name'].iloc[0]
                    
                    st.subheader("🎵 Track Information")
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.markdown(f"**Song:** {song_name}")
                    with col2:
                        st.markdown(f"**Artist:** {artist_name}")
                    with col3:
                        st.markdown(f"**Data Type:** {data_type.capitalize()}")
                    
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
                    
                    # Process data with AI if enabled, otherwise show basic analysis
                    st.subheader("📈 Key Insights")
                    if enable_ai and ai_helper:
                        try:
                            with st.spinner("Analyzing data with AI..."):
                                insights = ai_helper.analyze_track_data(df.to_dict("records"))
                            st.write(insights)
                        except Exception as e:
                            st.error(f"Error analyzing data with AI: {str(e)}")
                            if "Rate limit" in str(e):
                                st.warning("OpenAI API rate limit reached. Please wait a few minutes and try again.")
                            elif "Incorrect API key" in str(e):
                                st.warning("Invalid API key. Please check your OpenAI API key in the sidebar.")
                            # Fallback to basic analysis
                            st.write(basic_analysis(df, data_type))
                    else:
                        st.write(basic_analysis(df, data_type))
                    
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
    
    else:  # Country Charts
        st.markdown("""
        View streaming charts for specific countries.
        
        **Available Countries:**
        - US (United States)
        - GB (United Kingdom)
        - Global (Worldwide)
        """)
        
        # Country selector
        country_code = st.selectbox(
            "Select Country",
            ["us", "gb", "global"],
            format_func=lambda x: x.upper()
        )
        
        if country_code:
            try:
                with st.spinner(f"Fetching {data_type} chart data for {country_code.upper()}..."):
                    df = scraper.scrape_country_chart(country_code, data_type)
                
                if df is not None and not df.empty:
                    st.subheader(f"📊 {country_code.upper()} {data_type.capitalize()} Charts")
                    
                    # Display the chart data
                    st.dataframe(df, height=600)
                    
                    # Process data with AI if enabled
                    if enable_ai and ai_helper:
                        st.subheader("🤖 AI Analysis")
                        try:
                            with st.spinner("Analyzing chart data..."):
                                insights = ai_helper.analyze_chart_data(df.to_dict("records"))
                            st.write(insights)
                        except Exception as e:
                            st.error(f"Error analyzing data with AI: {str(e)}")
                    
                else:
                    st.error(f"❌ No data found for {country_code.upper()} {data_type} charts.")
                    
            except Exception as e:
                st.error(f"Error fetching country chart: {str(e)}")

if __name__ == "__main__":
    main() 