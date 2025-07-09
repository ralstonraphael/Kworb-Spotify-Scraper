# Spotify Chart Analyzer

<div align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/168px-Spotify_logo_without_text.svg.png" width="120px" />
  
  <h3>Powerful Spotify Chart Analysis with AI Insights</h3>
  
  <p>Track streaming performance, analyze trends, and get AI-powered insights for any Spotify track.</p>

  <p>
    <a href="#features">Features</a> •
    <a href="#installation">Installation</a> •
    <a href="#usage">Usage</a> •
    <a href="#development">Development</a> •
    <a href="#contributing">Contributing</a>
  </p>
</div>

## ✨ Features

- **Real-time Chart Data** - Get up-to-date streaming numbers from Spotify charts
- **Global Market Analysis** - Track performance across different regions
- **AI-Powered Insights** - Get intelligent analysis of streaming patterns and trends
- **Beautiful Visualization** - Modern, interactive charts and metrics
- **Easy to Use** - Simple interface with support for various URL formats
- **Detailed Metrics** - Comprehensive streaming data with historical trends

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- OpenAI API key for AI insights
- Chrome/Chromium for web scraping

### Installation

1. Clone the repository:

```bash
git clone https://github.com/ralstonraphael/Website_Scraper.git
cd Website_Scraper
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

4. Set up your environment variables:

```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

## 💫 Usage

1. Start the Streamlit app:

```bash
streamlit run src/ui/streamlit_app.py
```

2. Open your browser and navigate to the displayed URL (usually http://localhost:8501)

3. Enter your OpenAI API key in the settings sidebar

4. Paste a Spotify track URL to analyze its performance

### Supported URL Formats

- Full URL: `https://open.spotify.com/track/...`
- Spotify URI: `spotify:track:...`
- Track ID: Just the ID string

## 🛠 Development

### Project Structure

```
Website_Scraper/
├── data/               # Data storage
│   ├── processed/      # Cleaned and processed data
│   └── raw/           # Raw scraped data
├── src/               # Source code
│   ├── ui/            # Streamlit frontend
│   ├── scraper.py     # Data scraping logic
│   ├── cleaner.py     # Data cleaning utilities
│   └── ai_helper.py   # AI analysis tools
├── tests/             # Test suite
└── requirements.txt   # Project dependencies
```

### Running Tests

```bash
pytest tests/
```

### Code Style

This project follows PEP 8 guidelines. Format your code using:

```bash
black src/ tests/
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web framework
- [OpenAI](https://openai.com/) for powering our AI insights
- [Spotify](https://spotify.com/) for their incredible platform

---

<div align="center">
  Made with ❤️ by <a href="https://github.com/ralstonraphael">Ralston Raphael</a>
</div>
