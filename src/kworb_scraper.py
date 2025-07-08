"""
KWORB.net Spotify Charts Scraper
-------------------------------
Scrapes streaming data from KWORB.net using Selenium with robust error handling.
Author: Ralston Raphael
"""

import logging
from datetime import datetime
import time
import csv
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kworb_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TrackData:
    """Container for track data"""
    track_id: str
    name: str
    url: str
    streams: Optional[int] = None
    error: Optional[str] = None

class KworbScraper:
    """Scrapes streaming data from KWORB.net with robust error handling"""
    
    def __init__(self, headless: bool = True, retry_count: int = 3, timeout: int = 10):
        self.headless = headless
        self.retry_count = retry_count
        self.timeout = timeout
        self.driver = self.init_driver()
        self.wait = WebDriverWait(self.driver, timeout)
        
    def init_driver(self) -> webdriver.Chrome:
        """Initialize Chrome WebDriver with optimal settings"""
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')  # New headless mode
        
        # Essential options for stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # Mimic real browser
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def wait_for_element(
        self, 
        locator_chain: List[Tuple[str, str]], 
        timeout: Optional[int] = None,
        check_visibility: bool = True
    ) -> Optional[webdriver.remote.webelement.WebElement]:
        """
        Try multiple locators with explicit wait until element is found.
        Returns None if element not found after all attempts.
        """
        timeout = timeout or self.timeout
        last_exception = None
        
        for by, locator in locator_chain:
            try:
                if check_visibility:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.visibility_of_element_located((by, locator))
                    )
                else:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((by, locator))
                    )
                return element
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                last_exception = e
                logger.debug(f"Locator {by}='{locator}' failed: {str(e)}")
                continue
        
        if last_exception:
            logger.warning(f"All locators failed. Last error: {str(last_exception)}")
        return None

    def safe_click(self, element: webdriver.remote.webelement.WebElement, retries: int = 3) -> bool:
        """Safely click element with retries and scroll"""
        if not element:
            return False
            
        for attempt in range(retries):
            try:
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)  # Let scroll complete
                
                # Try regular click first
                try:
                    element.click()
                except:
                    # Fallback to JS click
                    self.driver.execute_script("arguments[0].click();", element)
                
                return True
            except Exception as e:
                logger.warning(f"Click attempt {attempt + 1} failed: {str(e)}")
                if attempt == retries - 1:
                    return False
                time.sleep(1)
        return False

    def extract_streams(self, track: TrackData) -> Optional[Dict]:
        """Extract streaming data for a track with retries"""
        logger.info(f"Processing track: {track.name} ({track.track_id})")
        
        for attempt in range(self.retry_count):
            try:
                # Load page
                self.driver.get(track.url)
                time.sleep(2)  # Initial load
                
                # Try multiple locator strategies for Streams link
                streams_locators = [
                    (By.LINK_TEXT, "Streams"),
                    (By.PARTIAL_LINK_TEXT, "Stream"),
                    (By.XPATH, "//a[contains(text(), 'Streams')]"),
                    (By.XPATH, "//a[normalize-space()='Streams']"),
                    (By.CSS_SELECTOR, "a[href*='streams']")
                ]
                
                streams_link = self.wait_for_element(streams_locators)
                if streams_link and self.safe_click(streams_link):
                    logger.debug("Clicked Streams link successfully")
                    time.sleep(1)  # Wait for table load
                
                # Try multiple locator strategies for table
                table_locators = [
                    (By.CSS_SELECTOR, "table"),  # Simple table
                    (By.XPATH, "//table[.//th[contains(text(), 'Date')] and .//th[contains(text(), 'Global')]]"),
                    (By.CSS_SELECTOR, "table:has(th:contains('Date')):has(th:contains('Global'))")
                ]
                
                table = self.wait_for_element(table_locators)
                if not table:
                    raise NoSuchElementException("Could not find streams table")
                
                # Extract data
                rows = table.find_elements(By.TAG_NAME, "tr")
                if not rows:
                    raise NoSuchElementException("No data rows found in table")
                
                # Get header indices
                headers = [cell.text.strip() for cell in rows[0].find_elements(By.TAG_NAME, "th")]
                try:
                    date_idx = headers.index('Date')
                    global_idx = headers.index('Global')
                except ValueError:
                    raise NoSuchElementException("Required columns not found in table")
                
                # Process rows
                data = []
                for row in rows[1:]:  # Skip header
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if not cells:
                            continue
                            
                        date = cells[date_idx].text.strip()
                        streams = cells[global_idx].text.strip()
                        
                        # Skip total/peak rows
                        if date.lower() in ['total', 'peak']:
                            continue
                            
                        # Clean streams value
                        streams = int(streams.replace(',', '')) if streams != '--' else 0
                        
                        data.append({
                            'track_id': track.track_id,
                            'track_name': track.name,
                            'date': date,
                            'streams': streams
                        })
                        
                    except (IndexError, ValueError, StaleElementReferenceException) as e:
                        logger.warning(f"Error processing row: {str(e)}")
                        continue
                
                if data:
                    return data
                raise NoSuchElementException("No valid data rows found")
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for track {track.track_id}: {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                track.error = str(e)
                return None
        
        return None

    def process_tracks(self, tracks: List[TrackData], output_file: str):
        """Process multiple tracks and save to CSV"""
        successful = 0
        failed = 0
        
        # Create/open output file
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['track_id', 'track_name', 'date', 'streams'])
            writer.writeheader()
            
            for track in tracks:
                data = self.extract_streams(track)
                if data:
                    for row in data:
                        writer.writerow(row)
                    successful += 1
                else:
                    failed += 1
                    logger.error(f"Failed to process track: {track.name} - {track.error}")
        
        logger.info(f"Job completed! Processed {len(tracks)} tracks - Success: {successful}, Failed: {failed}")
        return successful, failed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure browser closes properly"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    """Main entry point"""
    # Example tracks
    tracks = [
        TrackData(
            track_id="42UBPzRMh5yyz0EDPr6fr1",
            name="Example Track 1",
            url="https://kworb.net/spotify/track/42UBPzRMh5yyz0EDPr6fr1.html"
        ),
        # Add more tracks...
    ]
    
    output_file = "spotify_streams.csv"
    
    try:
        with KworbScraper(headless=True, retry_count=3, timeout=10) as scraper:
            successful, failed = scraper.process_tracks(tracks, output_file)
            
        if failed > 0:
            logger.warning(f"⚠️ {failed} tracks failed to process")
        logger.info(f"✅ Data saved to {output_file}")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 