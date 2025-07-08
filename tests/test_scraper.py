"""
Tests for the scraper module.
"""
import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from src.scraper import ChartScraper, ScrapingError

@pytest.fixture
def mock_response():
    """Create a mock response with sample HTML."""
    html = """
    <html>
        <body>
            <select name="week">
                <option value="2023-01-01">2023-01-01</option>
                <option value="2023-01-08">2023-01-08</option>
            </select>
            <table>
                <tr>
                    <th>Song</th>
                    <th>Artist</th>
                    <th>Streams</th>
                </tr>
                <tr>
                    <td><a href="/track/123">Test Song</a></td>
                    <td>Test Artist</td>
                    <td>1,234,567</td>
                </tr>
            </table>
        </body>
    </html>
    """
    return MagicMock(text=html, status_code=200)

@pytest.fixture
def scraper():
    """Create a ChartScraper instance."""
    return ChartScraper()

def test_init_scraper():
    """Test scraper initialization."""
    scraper = ChartScraper()
    assert scraper.driver is None
    
    with patch('selenium.webdriver.Chrome') as mock_chrome:
        scraper = ChartScraper(use_selenium=True)
        assert mock_chrome.called

def test_discover_available_weeks(scraper, mock_response):
    """Test discovering available chart weeks."""
    with patch('requests.Session.get', return_value=mock_response):
        dates = scraper.discover_available_weeks()
        assert len(dates) == 2
        assert dates[0] == datetime.datetime(2023, 1, 1)
        assert dates[1] == datetime.datetime(2023, 1, 8)

def test_scrape_week(scraper, mock_response):
    """Test scraping a single week's data."""
    with patch('requests.Session.get', return_value=mock_response):
        date = datetime.datetime(2023, 1, 1)
        df = scraper.scrape_week(date)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]['song_title'] == 'Test Song'
        assert df.iloc[0]['artist'] == 'Test Artist'
        assert df.iloc[0]['streams'] == 1234567

def test_parse_streams():
    """Test stream count parsing."""
    assert ChartScraper._parse_streams("1,234,567") == 1234567
    assert ChartScraper._parse_streams("invalid") == 0
    assert ChartScraper._parse_streams("") == 0

def test_validate_data():
    """Test data validation."""
    valid_data = pd.DataFrame({
        'chart_date': ['2023-01-01'],
        'rank': [1],
        'song_title': ['Test Song'],
        'artist': ['Test Artist'],
        'streams': [1234567],
        'track_url': ['/track/123']
    })
    
    # Should not raise an exception
    ChartScraper._validate_data(valid_data)
    
    # Should raise an exception for missing columns
    invalid_data = pd.DataFrame({
        'song_title': ['Test Song'],
        'artist': ['Test Artist']
    })
    
    with pytest.raises(ScrapingError):
        ChartScraper._validate_data(invalid_data)
    
    # Should raise an exception for empty DataFrame
    empty_data = pd.DataFrame()
    with pytest.raises(ScrapingError):
        ChartScraper._validate_data(empty_data)

def test_scrape_date_range(scraper, mock_response, tmp_path):
    """Test scraping a date range."""
    with patch('requests.Session.get', return_value=mock_response):
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 1, 8)
        
        df = scraper.scrape_date_range(
            start_date,
            end_date,
            output_dir=Path(tmp_path)
        )
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # One entry for each week
        assert all(col in df.columns for col in [
            'chart_date', 'rank', 'song_title', 'artist', 'streams', 'track_url'
        ])

def test_error_handling(scraper):
    """Test error handling for failed requests."""
    with patch('requests.Session.get', side_effect=Exception("Test error")):
        with pytest.raises(ScrapingError):
            scraper.discover_available_weeks()

def test_selenium_fallback():
    """Test Selenium fallback functionality."""
    with patch('selenium.webdriver.Chrome') as mock_chrome:
        mock_driver = MagicMock()
        mock_driver.page_source = "<html><body>Test</body></html>"
        mock_chrome.return_value = mock_driver
        
        scraper = ChartScraper(use_selenium=True)
        
        with patch('requests.Session.get', side_effect=Exception("Test error")):
            result = scraper._make_request("http://test.com")
            assert isinstance(result, BeautifulSoup)
            assert mock_driver.get.called 