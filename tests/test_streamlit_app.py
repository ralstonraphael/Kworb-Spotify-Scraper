"""
Tests for the Streamlit UI application.
"""
import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import streamlit as st

from src.ui import streamlit_app

@pytest.fixture
def sample_data():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        'chart_date': ['2023-01-01', '2023-01-08'],
        'rank': [1, 2],
        'song_title': ['Test Song', 'Another Song'],
        'artist': ['Test Artist', 'Another Artist'],
        'streams': [1234567, 890123],
        'track_url': ['/track/123', '/track/456']
    })

@pytest.fixture
def mock_scraper():
    """Create mock ChartScraper."""
    with patch('src.ui.streamlit_app.ChartScraper') as mock:
        mock_instance = MagicMock()
        mock_instance.discover_available_weeks.return_value = [
            datetime.datetime(2023, 1, 1),
            datetime.datetime(2023, 1, 8)
        ]
        mock.return_value = mock_instance
        yield mock_instance

def test_load_available_dates(mock_scraper):
    """Test loading available dates."""
    dates = streamlit_app.load_available_dates()
    assert len(dates) == 2
    assert dates[0] == datetime.datetime(2023, 1, 1)
    assert dates[1] == datetime.datetime(2023, 1, 8)
    assert mock_scraper.discover_available_weeks.called

def test_apply_filters(sample_data):
    """Test data filtering functionality."""
    filters = {
        'min_streams': 1000000,
        'search_term': 'Test',
        'top_n': 1
    }
    
    filtered = streamlit_app.apply_filters(sample_data, filters)
    
    # Check minimum streams filter
    assert all(filtered['streams'] >= filters['min_streams'])
    
    # Check search filter
    assert all(
        filtered['artist'].str.contains('Test', case=False) |
        filtered['song_title'].str.contains('Test', case=False)
    )
    
    # Check top N filter
    assert len(filtered) == 1

def test_display_data_preview(sample_data):
    """Test data preview display."""
    with patch('streamlit.dataframe') as mock_dataframe:
        streamlit_app.display_data_preview(sample_data)
        assert mock_dataframe.called

@patch('streamlit.sidebar.date_input')
@patch('streamlit.sidebar.checkbox')
def test_date_selector(mock_checkbox, mock_date_input, mock_scraper):
    """Test date range selector."""
    mock_checkbox.return_value = False
    mock_date_input.side_effect = [
        datetime.date(2023, 1, 1),
        datetime.date(2023, 1, 8)
    ]
    
    start_date, end_date = streamlit_app.date_selector()
    
    assert start_date == datetime.datetime(2023, 1, 1)
    assert end_date == datetime.datetime(2023, 1, 8)
    assert mock_date_input.call_count == 2

def test_filter_controls():
    """Test filter control widgets."""
    with patch('streamlit.sidebar.number_input') as mock_number_input, \
         patch('streamlit.sidebar.text_input') as mock_text_input:
        
        mock_number_input.side_effect = [1000, 10]
        mock_text_input.return_value = "Test"
        
        filters = streamlit_app.filter_controls()
        
        assert filters['min_streams'] == 1000
        assert filters['search_term'] == "Test"
        assert filters['top_n'] == 10
        assert mock_number_input.call_count == 2
        assert mock_text_input.call_count == 1

def test_export_controls():
    """Test export format selection."""
    with patch('streamlit.sidebar.checkbox') as mock_checkbox:
        mock_checkbox.side_effect = [True, False, True, False]
        
        formats = streamlit_app.export_controls()
        
        assert 'csv' in formats
        assert 'excel' not in formats
        assert 'json' in formats
        assert 'parquet' not in formats
        assert mock_checkbox.call_count == 4 