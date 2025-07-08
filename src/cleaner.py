"""
Data cleaning and processing module for Spotify chart data.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

import pandas as pd
from tqdm import tqdm

from src import config
from .ai_helper import AIHelper

logger = logging.getLogger(__name__)

class DataCleaningError(Exception):
    """Custom exception for data cleaning errors."""
    pass

class DataCleaner:
    """
    Handles data cleaning and processing of scraped Spotify chart data.
    """
    
    def __init__(self, raw_data_dir: Optional[Path] = None):
        """
        Initialize the data cleaner.
        
        Args:
            raw_data_dir (Optional[Path]): Directory containing raw CSV files
        """
        self.raw_data_dir = raw_data_dir or config.RAW_DATA_DIR
        self.ai_helper = AIHelper()
    
    def load_raw_files(self) -> pd.DataFrame:
        """
        Load and combine all raw CSV files.
        
        Returns:
            pd.DataFrame: Combined raw data
        """
        logger.info(f"Loading raw files from {self.raw_data_dir}")
        csv_files = list(self.raw_data_dir.glob("chart_*.csv"))
        
        if not csv_files:
            raise DataCleaningError(f"No CSV files found in {self.raw_data_dir}")
        
        all_data = []
        for file in tqdm(csv_files, desc="Loading files"):
            try:
                df = pd.read_csv(file)
                all_data.append(df)
            except Exception as e:
                logger.error(f"Failed to load {file}: {e}")
                continue
        
        if not all_data:
            raise DataCleaningError("No data could be loaded from CSV files")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"Loaded {len(combined_df)} rows from {len(csv_files)} files")
        return combined_df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the data.
        
        Args:
            df (pd.DataFrame): Raw data to clean
            
        Returns:
            pd.DataFrame: Cleaned data
        """
        logger.info("Starting data cleaning process")
        
        try:
            # Create a copy to avoid modifying the original
            cleaned = df.copy()
            
            # Convert chart_date to datetime and store in standard format
            cleaned['chart_date'] = pd.to_datetime(cleaned['chart_date'])
            
            # Ensure we have the numeric date format
            if 'date_numeric' not in cleaned.columns:
                cleaned['date_numeric'] = cleaned['chart_date'].dt.strftime('%Y%m%d')
            
            # Clean song titles
            cleaned['song_title'] = cleaned['song_title'].str.strip()
            
            # Clean artist names
            cleaned['artist'] = cleaned['artist'].apply(self._clean_artist_name)
            
            # Ensure streams is numeric
            cleaned['streams'] = pd.to_numeric(cleaned['streams'], errors='coerce').fillna(0).astype(int)
            
            # Clean artist URLs
            cleaned['artist_url'] = cleaned['artist_url'].fillna('')
            
            # Clean artist IDs
            cleaned['artist_id'] = cleaned['artist_id'].fillna('')
            
            # Ensure rank is integer
            cleaned['rank'] = cleaned['rank'].astype(int)
            
            # Reorder columns to put dates first
            column_order = [
                'chart_date',
                'date_numeric',
                'rank',
                'artist',
                'song_title',
                'streams',
                'artist_url',
                'artist_id'
            ]
            cleaned = cleaned[column_order]
            
            # Use AI to clean and format the data
            cleaned_data = self.ai_helper.clean_and_format_data(cleaned.to_dict('records'))
            
            # Convert to DataFrame
            df = pd.DataFrame(cleaned_data)
            
            # Get AI insights about the data
            insights = self.ai_helper.analyze_chart_data(cleaned_data)
            if insights.get("status") == "success":
                print("AI Insights:", insights["insights"])
            
            # Get visualization suggestions
            viz_suggestions = self.ai_helper.suggest_visualizations(df.dtypes.to_dict())
            if viz_suggestions:
                print("\nRecommended visualizations:")
                for suggestion in viz_suggestions:
                    print(f"- {suggestion}")
            
            logger.info("Data cleaning completed successfully")
            return df
            
        except Exception as e:
            logger.error(f"Data cleaning failed: {e}")
            raise DataCleaningError("Failed to clean data") from e
    
    @staticmethod
    def _clean_artist_name(artist: str) -> str:
        """
        Clean and standardize artist names.
        
        Args:
            artist (str): Raw artist name
            
        Returns:
            str: Cleaned artist name
        """
        if pd.isna(artist):
            return ""
        
        # Convert to string if not already
        artist = str(artist).strip()
        
        # Handle featuring artists
        featuring_variants = ['feat.', 'ft.', 'featuring', 'with', '&']
        for variant in featuring_variants:
            artist = artist.replace(variant, 'feat.')
        
        # Remove extra whitespace
        artist = ' '.join(artist.split())
        
        return artist
    
    def deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate entries from the dataset.
        
        Args:
            df (pd.DataFrame): Data to deduplicate
            
        Returns:
            pd.DataFrame: Deduplicated data
        """
        logger.info("Starting deduplication process")
        
        try:
            # Sort by date and rank to keep the latest version of duplicates
            sorted_df = df.sort_values(['chart_date', 'rank'])
            
            # Remove exact duplicates
            deduped = sorted_df.drop_duplicates(
                subset=['chart_date', 'rank', 'song_title', 'artist'],
                keep='last'
            )
            
            removed_count = len(df) - len(deduped)
            logger.info(f"Removed {removed_count} duplicate entries")
            
            return deduped
            
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            raise DataCleaningError("Failed to deduplicate data") from e
    
    def export_final(
        self,
        df: pd.DataFrame,
        output_file: Optional[Path] = None,
        formats: Optional[List[str]] = None
    ) -> None:
        """
        Export the final processed data.
        
        Args:
            df (pd.DataFrame): Data to export
            output_file (Optional[Path]): Output file path (without extension)
            formats (Optional[List[str]]): List of formats to export (csv, excel, json, parquet)
        """
        output_file = output_file or config.PROCESSED_DATA_DIR / "all_charts"
        formats = formats or ['csv']
        
        logger.info(f"Exporting final data to {output_file}")
        
        try:
            for fmt in formats:
                fmt = fmt.lower()
                out_path = output_file.with_suffix(f".{fmt}")
                
                if fmt == 'csv':
                    df.to_csv(out_path, index=False)
                elif fmt == 'excel':
                    df.to_excel(out_path, index=False)
                elif fmt == 'json':
                    df.to_json(out_path, orient='records', lines=True)
                elif fmt == 'parquet':
                    df.to_parquet(out_path, index=False)
                else:
                    logger.warning(f"Unsupported format: {fmt}")
                    continue
                
                logger.info(f"Exported data to {out_path}")
                
        except Exception as e:
            logger.error(f"Data export failed: {e}")
            raise DataCleaningError("Failed to export data") from e
    
    def process_all(
        self,
        output_formats: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Process all data from raw files to final output.
        
        Args:
            output_formats (Optional[List[str]]): List of output formats
            
        Returns:
            pd.DataFrame: Final processed data
        """
        logger.info("Starting full data processing pipeline")
        
        try:
            # Load raw data
            raw_df = self.load_raw_files()
            
            # Clean data
            cleaned_df = self.clean_data(raw_df)
            
            # Remove duplicates
            final_df = self.deduplicate(cleaned_df)
            
            # Export in requested formats
            self.export_final(final_df, formats=output_formats)
            
            logger.info("Data processing pipeline completed successfully")
            return final_df
            
        except Exception as e:
            logger.error(f"Data processing pipeline failed: {e}")
            raise DataCleaningError("Failed to process data") from e 