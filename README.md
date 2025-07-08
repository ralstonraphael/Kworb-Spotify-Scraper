# Spotify Chart History Scraper

A sleek, modern tool to analyze Spotify streaming data from KWORB.net with precision and elegance.

## Overview

This application provides a streamlined interface to track and analyze Spotify streaming performance. It captures historical streaming data with a focus on global and US markets, presenting insights through clean, interactive visualizations.

## Features

- **Track Analysis**: Enter any Spotify track URL or ID to view its streaming history
- **Data Visualization**: Interactive charts showing streaming performance over time
- **Market Comparison**: Side-by-side analysis of global and US performance
- **Data Export**: Download complete streaming history in CSV format
- **Clean Interface**: Minimalist design focused on data clarity

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/yourusername/spotify-chart-scraper.git
cd spotify-chart-scraper
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_api_key_here
```

4. Run the application:

```bash
streamlit run src/ui/streamlit_app.py
```

## Usage

1. Launch the application
2. Enter a Spotify track URL or KWORB URL in the sidebar
3. View streaming history, visualizations, and download data as needed

## Requirements

- Python 3.10+
- Chrome/Chromium browser
- OpenAI API key for data processing

## Data Structure

The application captures:

- Total streams (Global and US)
- Peak streams
- Daily streaming data
- Chart entry and exit dates

## Contributing

We welcome contributions that maintain the project's minimalist and elegant approach. Please ensure your code follows the existing style and includes appropriate tests.

## License

MIT License. See [LICENSE](LICENSE) for details.
