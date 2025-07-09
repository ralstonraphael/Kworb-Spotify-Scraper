# Spotify Chart Analyzer

A tool for analyzing Spotify track performance data using data from KWORB.net. This tool provides insights into streaming performance, trends, and market-specific data.

## Features

- Track streaming history visualization
- Global and market-specific performance metrics
- AI-powered insights (requires OpenAI API key)
- Interactive data exploration
- Beautiful Streamlit UI

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ralstonraphael/Website_Scraper.git
cd Website_Scraper
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install system dependencies (if needed):

```bash
# On Ubuntu/Debian:
sudo apt-get update
sudo apt-get install -y chromium-browser

# On macOS:
brew install --cask chromium

# For better performance on macOS:
xcode-select --install
pip install watchdog
```

## Usage

1. Start the Streamlit app:

```bash
streamlit run main.py
```

2. Enter your OpenAI API key in the sidebar (required for AI insights)

3. Enter a Spotify track URL in one of these formats:

   - Full URL: `https://open.spotify.com/track/...`
   - Spotify URI: `spotify:track:...`
   - Track ID: Just the ID

4. View the analysis results:
   - Track Information
   - Performance Metrics
   - Key Insights
   - Streaming History Chart
   - Full Data Table

## Project Structure

```
.
├── src/
│   ├── ui/
│   │   └── streamlit_app.py    # Main Streamlit application
│   ├── ai_helper.py            # AI analysis functionality
│   ├── scraper.py             # Web scraping functionality
│   ├── cleaner.py            # Data cleaning utilities
│   └── config.py             # Configuration settings
├── data/
│   ├── raw/                  # Raw scraped data
│   └── processed/            # Processed data
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── packages.txt            # System dependencies
└── README.md              # This file
```

## Configuration

The app can be configured through:

1. Environment Variables (create a `.env` file):

```
OPENAI_API_KEY=your_api_key_here
```

2. Streamlit Settings (`.streamlit/config.toml`):

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

3. Application Settings (`src/config.py`)

## Development

1. Install in development mode:

```bash
pip install -e .
```

2. Run tests:

```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [KWORB.net](https://kworb.net/) for providing Spotify chart data
- [Streamlit](https://streamlit.io/) for the amazing UI framework
- [OpenAI](https://openai.com/) for the AI capabilities
