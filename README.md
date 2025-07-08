# Kworb Spotify Scraper

A modern, elegant tool for scraping and analyzing Spotify chart data from KWORB.net, featuring AI-powered data cleaning and structuring.

## Features

- 🔍 Scrapes Spotify chart data from KWORB.net
- 🤖 AI-powered data cleaning and formatting
- 📊 Clean data presentation through Streamlit UI
- 🌍 Global and US streaming data tracking
- 📈 Historical trend analysis

## Setup

1. Clone the repository:

```bash
git clone https://github.com/ralstonraphael/Kworb-Spotify-Scraper.git
cd Kworb-Spotify-Scraper
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment:
   - Create `.streamlit/secrets.toml`
   - Add your OpenAI API key:
     ```toml
     OPENAI_API_KEY = "your-api-key"
     ```

## Usage

Run the Streamlit app:

```bash
streamlit run src/ui/streamlit_app.py
```

## Project Structure

```
Kworb-Spotify-Scraper/
├── data/               # Data storage
├── src/               # Source code
│   ├── ai_helper.py   # AI processing
│   ├── cleaner.py    # Data cleaning
│   ├── scraper.py    # Web scraping
│   └── ui/           # Streamlit interface
└── tests/            # Test suite
```

## Requirements

- Python 3.8+
- Chrome/Chromium browser
- OpenAI API key
- Internet connection

## License

This project is licensed under the terms of the MIT license.
