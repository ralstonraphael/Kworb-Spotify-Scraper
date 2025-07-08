#!/usr/bin/env python3
"""
Main entry point for the Spotify Chart Scraper application.
"""
import argparse
import logging
from datetime import datetime
from pathlib import Path

import streamlit.web.cli as stcli
import sys

from src import config
from src.cleaner import DataCleaner
from src.scraper import ChartScraper

# Configure logging
logging.basicConfig(
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    try:
        return datetime.strptime(date_str, config.DATE_FORMAT)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Invalid date format. Please use {config.DATE_FORMAT}"
        ) from e

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Spotify Chart History Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch the Streamlit UI"
    )
    
    parser.add_argument(
        "--start-date",
        type=parse_date,
        help=f"Start date (format: {config.DATE_FORMAT})"
    )
    
    parser.add_argument(
        "--end-date",
        type=parse_date,
        help=f"End date (format: {config.DATE_FORMAT})"
    )
    
    parser.add_argument(
        "--no-selenium",
        action="store_true",
        help="Disable Selenium (not recommended)"
    )
    
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["csv", "excel", "json", "parquet"],
        default=["csv"],
        help="Output formats (default: csv)"
    )
    
    return parser.parse_args()

def launch_ui():
    """Launch the Streamlit UI."""
    logger.info("Launching Streamlit UI...")
    sys.argv = ["streamlit", "run", str(Path(__file__).parent / "src/ui/streamlit_app.py")]
    sys.exit(stcli.main())

def run_cli(args: argparse.Namespace):
    """Run the application in CLI mode."""
    logger.info("Starting CLI scraping process...")
    
    try:
        # Initialize scraper (Selenium enabled by default)
        scraper = ChartScraper(use_selenium=not args.no_selenium)
        
        # Get date range
        if not (args.start_date and args.end_date):
            available_dates = scraper.discover_available_weeks()
            start_date = args.start_date or min(available_dates)
            end_date = args.end_date or max(available_dates)
        else:
            start_date = args.start_date
            end_date = args.end_date
        
        # Scrape data
        logger.info(f"Scraping data from {start_date} to {end_date}")
        df = scraper.scrape_date_range(
            start_date,
            end_date,
            output_dir=config.RAW_DATA_DIR
        )
        
        # Process and export data
        cleaner = DataCleaner()
        df = cleaner.clean_data(df)
        df = cleaner.deduplicate(df)
        cleaner.export_final(df, formats=args.formats)
        
        logger.info("Scraping completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.exception("Application error")
        sys.exit(1)

def main():
    """Main entry point."""
    args = parse_args()
    
    if args.ui:
        launch_ui()
    else:
        run_cli(args)

if __name__ == "__main__":
    main() 