"""Web scraping functionality for Spotify chart data."""
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Union

from src.config import KWORB_BASE_URL, WAIT_TIME, RETRY_COUNT

class ChartScraper:
    """Scraper for Spotify chart data."""
    
    def __init__(self, use_selenium: bool = True):
        """Initialize the scraper."""
        self.use_selenium = use_selenium
        self.driver = None
        if use_selenium:
            self._setup_driver()
    
    def _setup_driver(self):
        """Set up the Selenium WebDriver with Chrome."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={UserAgent().random}')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(WAIT_TIME)
        except Exception as e:
            logging.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def _get_url_for_track(self, track_id: str, data_type: str = "weekly") -> str:
        """Get the URL for a track's chart data."""
        base_url = f"{KWORB_BASE_URL}/track/{track_id}"
        if data_type == "daily":
            return f"{base_url}_daily.html"
        return f"{base_url}.html"
    
    def _switch_to_daily_view(self):
        """Switch to daily view if available."""
        try:
            # Try to find and click the daily button
            daily_button = self.driver.find_element(By.ID, "daily")
            if daily_button:
                daily_button.click()
                time.sleep(2)  # Wait for the view to update
                return True
        except NoSuchElementException:
            pass
        return False
    
    def _extract_table_data(self, table_element) -> pd.DataFrame:
        """Extract data from a table element into a DataFrame."""
        headers = []
        try:
            header_cells = table_element.find_elements(By.TAG_NAME, "th")
            headers = [cell.text.strip() for cell in header_cells]
        except NoSuchElementException:
            logging.warning("No header cells found in table")
            return pd.DataFrame()
        
        rows = []
        try:
            row_elements = table_element.find_elements(By.TAG_NAME, "tr")
            for row in row_elements:
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells:  # Skip header row
                    row_data = [cell.text.strip() for cell in cells]
                    if len(row_data) == len(headers):  # Only add rows that match header length
                        rows.append(row_data)
        except NoSuchElementException:
            logging.warning("No data rows found in table")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=headers)
        return df
    
    def scrape_track_history(self, track_id: str, data_type: str = "weekly") -> Optional[pd.DataFrame]:
        """Scrape streaming history for a track."""
        if not self.use_selenium or not self.driver:
            logging.error("Selenium WebDriver not initialized")
            return None
        
        url = self._get_url_for_track(track_id, data_type)
        retries = 0
        
        while retries < RETRY_COUNT:
            try:
                self.driver.get(url)
                
                # Wait for any table to load
                wait = WebDriverWait(self.driver, WAIT_TIME)
                table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                
                if data_type == "daily":
                    # Look for daily view container
                    daily_div = self.driver.find_element(By.CLASS_NAME, "daily")
                    if daily_div:
                        # Try to find table within daily div
                        table = daily_div.find_element(By.TAG_NAME, "table")
                    else:
                        # Try switching to daily view
                        if self._switch_to_daily_view():
                            # Wait for daily data to load
                            time.sleep(2)
                            daily_div = self.driver.find_element(By.CLASS_NAME, "daily")
                            table = daily_div.find_element(By.TAG_NAME, "table")
                
                # Extract track info
                try:
                    title_element = self.driver.find_element(By.TAG_NAME, "h1")
                    title = title_element.text.strip()
                    artist_element = self.driver.find_element(By.CSS_SELECTOR, "h1 + p")
                    artist = artist_element.text.strip()
                except NoSuchElementException:
                    logging.warning("Could not find track title or artist")
                    title = "Unknown"
                    artist = "Unknown"
                
                # Extract table data
                df = self._extract_table_data(table)
                
                if df.empty:
                    logging.warning("No data found in table")
                    retries += 1
                    time.sleep(2)  # Wait before retrying
                    continue
                
                # Add track info columns
                df['song_name'] = title
                df['artist_name'] = artist
                
                # Clean up numeric columns
                for col in df.columns:
                    if col not in ['date', 'song_name', 'artist_name']:
                        df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')
                
                return df
                
            except TimeoutException:
                logging.error(f"Timeout waiting for table to load: {url}")
                retries += 1
                time.sleep(2)  # Wait before retrying
            except Exception as e:
                logging.error(f"Error scraping track {track_id}: {e}")
                retries += 1
                time.sleep(2)  # Wait before retrying
        
        return None
    
    def __del__(self):
        """Clean up Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.warning(f"Error closing WebDriver: {e}") 