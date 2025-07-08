"""
Tests for the data cleaning module.
"""
import pandas as pd
import pytest
from pathlib import Path

from src.cleaner import DataCleaner, DataCleaningError

@pytest.fixture
def sample_data():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        'chart_date': ['2023-01-01', '2023-01-01', '2023-01-08'],
        'rank': [1, 2, 1],
        'song_title': [' Test Song ', 'Another Song', 'Test Song'],
        'artist': ['Test Artist ft. Other Artist', 'Solo Artist', 'Test Artist featuring Other Artist'],
        'streams': ['1,234,567', '890,123', '2,345,678'],
        'track_url': ['/track/123', '/track/456', '/track/123']
    })

@pytest.fixture
def cleaner(tmp_path):
    """Create DataCleaner instance with temporary directory."""
    return DataCleaner(raw_data_dir=tmp_path)

def test_init_cleaner(tmp_path):
    """Test cleaner initialization."""
    cleaner = DataCleaner(raw_data_dir=tmp_path)
    assert cleaner.raw_data_dir == tmp_path

def test_clean_data(cleaner, sample_data):
    """Test data cleaning functionality."""
    cleaned = cleaner.clean_data(sample_data)
    
    # Check date format
    assert all(pd.to_datetime(cleaned['chart_date']).dt.strftime('%Y-%m-%d') == cleaned['chart_date'])
    
    # Check song title cleaning
    assert cleaned['song_title'].iloc[0] == 'Test Song'
    
    # Check artist name standardization
    assert cleaned['artist'].iloc[0] == 'Test Artist feat. Other Artist'
    assert cleaned['artist'].iloc[2] == 'Test Artist feat. Other Artist'
    
    # Check stream count conversion
    assert cleaned['streams'].iloc[0] == 1234567
    assert cleaned['streams'].dtype == 'int64'
    
    # Check rank is integer
    assert cleaned['rank'].dtype == 'int64'

def test_clean_artist_name():
    """Test artist name cleaning."""
    test_cases = [
        ('Artist1 ft. Artist2', 'Artist1 feat. Artist2'),
        ('Artist1 featuring Artist2', 'Artist1 feat. Artist2'),
        ('Artist1 with Artist2', 'Artist1 feat. Artist2'),
        ('Artist1 & Artist2', 'Artist1 feat. Artist2'),
        ('  Artist1  ', 'Artist1'),
        ('', ''),
        (None, '')
    ]
    
    for input_name, expected in test_cases:
        assert DataCleaner._clean_artist_name(input_name) == expected

def test_deduplicate(cleaner, sample_data):
    """Test deduplication functionality."""
    # Add duplicate entry
    duplicate = pd.DataFrame({
        'chart_date': ['2023-01-01'],
        'rank': [1],
        'song_title': ['Test Song'],
        'artist': ['Test Artist ft. Other Artist'],
        'streams': ['1,234,567'],
        'track_url': ['/track/123']
    })
    
    data_with_duplicate = pd.concat([sample_data, duplicate], ignore_index=True)
    deduped = cleaner.deduplicate(data_with_duplicate)
    
    # Check number of rows
    assert len(deduped) == len(sample_data)
    
    # Check no exact duplicates exist
    assert not deduped.duplicated(subset=['chart_date', 'rank', 'song_title', 'artist']).any()

def test_load_raw_files(cleaner, sample_data, tmp_path):
    """Test loading raw CSV files."""
    # Create test CSV files
    file1 = tmp_path / "chart_2023-01-01.csv"
    file2 = tmp_path / "chart_2023-01-08.csv"
    
    sample_data.iloc[:2].to_csv(file1, index=False)
    sample_data.iloc[2:].to_csv(file2, index=False)
    
    # Load and verify
    loaded = cleaner.load_raw_files()
    assert len(loaded) == len(sample_data)
    assert all(col in loaded.columns for col in sample_data.columns)

def test_load_raw_files_no_files(cleaner):
    """Test loading from empty directory."""
    with pytest.raises(DataCleaningError):
        cleaner.load_raw_files()

def test_export_final(cleaner, sample_data, tmp_path):
    """Test data export functionality."""
    formats = ['csv', 'excel', 'json', 'parquet']
    cleaner.export_final(sample_data, output_file=tmp_path / "test_export", formats=formats)
    
    # Verify files were created
    assert (tmp_path / "test_export.csv").exists()
    assert (tmp_path / "test_export.xlsx").exists()
    assert (tmp_path / "test_export.json").exists()
    assert (tmp_path / "test_export.parquet").exists()
    
    # Verify CSV content
    loaded_csv = pd.read_csv(tmp_path / "test_export.csv")
    assert len(loaded_csv) == len(sample_data)
    assert all(col in loaded_csv.columns for col in sample_data.columns)

def test_process_all(cleaner, sample_data, tmp_path):
    """Test full processing pipeline."""
    # Create test input file
    input_file = tmp_path / "chart_2023-01-01.csv"
    sample_data.to_csv(input_file, index=False)
    
    # Process data
    result = cleaner.process_all(output_formats=['csv'])
    
    # Verify results
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(sample_data.drop_duplicates(
        subset=['chart_date', 'rank', 'song_title', 'artist']
    ))
    assert (tmp_path.parent / "processed" / "all_charts.csv").exists()

def test_error_handling(cleaner, sample_data):
    """Test error handling in data cleaning."""
    # Test with invalid data
    invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
    
    with pytest.raises(DataCleaningError):
        cleaner.clean_data(invalid_data)
    
    # Test with invalid export format
    with pytest.raises(Exception):
        cleaner.export_final(sample_data, formats=['invalid_format'])
    
    # Test with invalid file path
    with pytest.raises(Exception):
        cleaner.export_final(sample_data, output_file=Path('/invalid/path/test')) 