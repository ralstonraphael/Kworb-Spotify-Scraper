# KWORB Spotify Charts Scraper

A robust Python scraper for extracting streaming data from KWORB.net's Spotify Global Charts.

## Features

- 🚀 Fast and reliable with headless Chrome
- 🔄 Multiple retry strategies and fallback locators
- 📊 Clean CSV output with track history
- 🪵 Detailed logging and error handling
- 🛡️ Browser crash protection with context manager

## Installation

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

## Usage

1. Edit the `tracks` list in `src/kworb_scraper.py` with your target tracks:

```python
tracks = [
    TrackData(
        track_id="42UBPzRMh5yyz0EDPr6fr1",
        name="Example Track 1",
        url="https://kworb.net/spotify/track/42UBPzRMh5yyz0EDPr6fr1.html"
    ),
    # Add more tracks...
]
```

2. Run the scraper:

```bash
python src/kworb_scraper.py
```

The script will:

- Create a `kworb_scraper.log` file with detailed logs
- Output results to `spotify_streams.csv`
- Show progress and any errors in the console

## Configuration

You can adjust these parameters in `main()`:

- `headless`: Run Chrome in headless mode (default: True)
- `retry_count`: Number of retries per track (default: 3)
- `timeout`: Wait timeout in seconds (default: 10)

## Output Format

The CSV file contains:

- `track_id`: Spotify track ID
- `track_name`: Track name
- `date`: Stream date
- `streams`: Global stream count

## Error Handling

The scraper handles:

- Network issues
- Missing elements
- Stale elements
- Click failures
- Browser crashes

Failed tracks are logged with detailed error messages.

## Contributing

Pull requests welcome! Please ensure you:

1. Add tests for new features
2. Update documentation
3. Follow the existing code style

## License

MIT License - see LICENSE file for details
