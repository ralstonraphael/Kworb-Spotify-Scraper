"""Web scraping functionality for Spotify chart data."""
import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.expected_conditions import presence_of_element_located, visibility_of_element_located
from fake_useragent import UserAgent
import logging
import time
import random
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
        options.add_argument('--headless=new')  # Use new headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Add random user agent
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'user-agent={user_agent}')
        
        # Add additional headers
        options.add_argument('--accept-language=en-US,en;q=0.9')
        options.add_argument('--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent,
                "platform": "MacIntel",
                "acceptLanguage": "en-US,en;q=0.9"
            })
            
            # Add webdriver detection evasion
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = {
                    runtime: {}
                };
            """)
            
            self.driver.implicitly_wait(WAIT_TIME)
        except Exception as e:
            logging.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def _random_sleep(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to simulate human behavior."""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def _simulate_human_behavior(self):
        """Simulate human-like behavior on the page."""
        try:
            # Random scroll
            scroll_amount = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            self._random_sleep(0.5, 1.5)
            
            # Random mouse movements
            actions = ActionChains(self.driver)
            for _ in range(random.randint(2, 5)):
                x = random.randint(0, 500)
                y = random.randint(0, 500)
                actions.move_by_offset(x, y)
                self._random_sleep(0.1, 0.3)
            
            # Sometimes move back to top
            if random.random() < 0.3:
                self.driver.execute_script("window.scrollTo(0, 0);")
                self._random_sleep(0.5, 1.0)
        except Exception as e:
            logging.warning(f"Error during human behavior simulation: {e}")
    
    def _get_url_for_track(self, track_id: str) -> str:
        """Get the URL for a track's chart data."""
        return f"{KWORB_BASE_URL}/track/{track_id}.html"
    
    def _get_url_for_country(self, country_code: str, data_type: str = "daily") -> str:
        """Get the URL for a country's chart data."""
        return f"{KWORB_BASE_URL}/country/{country_code}_{data_type}.html"
    
    def _wait_for_page_load(self):
        """Wait for the page to be fully loaded."""
        try:
            # Wait for the document to be ready
            self.driver.execute_script("""
                return new Promise((resolve) => {
                    if (document.readyState === 'complete') {
                        resolve();
                    } else {
                        window.addEventListener('load', resolve);
                    }
                });
            """)
            
            # Add random delay
            self._random_sleep(1.0, 2.0)
            
            # Wait for any table to be present
            WebDriverWait(self.driver, WAIT_TIME).until(
                presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Simulate human behavior
            self._simulate_human_behavior()
            
            return True
        except Exception as e:
            logging.error(f"Error waiting for page load: {e}")
            return False
    
    def _extract_cell_value(self, cell) -> str:
        """Extract value from a cell, handling both simple and nested span structures."""
        try:
            # First try to find the span with class 's' (daily view)
            value_span = cell.find_element(By.CSS_SELECTOR, "span.s")
            if value_span:
                return value_span.text.strip()
        except NoSuchElementException:
            # If no span.s found, try direct cell text (weekly view)
            return cell.text.strip()
        except Exception as e:
            logging.warning(f"Error extracting cell value: {e}")
            return ""
    
    def _extract_table_data(self, table_element) -> pd.DataFrame:
        """Extract data from a table element into a DataFrame."""
        headers = []
        try:
            header_cells = table_element.find_elements(By.TAG_NAME, "th")
            headers = [cell.text.strip() for cell in header_cells]
            logging.info(f"Found {len(headers)} columns: {headers}")
        except NoSuchElementException:
            logging.warning("No header cells found in table")
            return pd.DataFrame()
        
        rows = []
        try:
            row_elements = table_element.find_elements(By.TAG_NAME, "tr")
            logging.info(f"Found {len(row_elements)} rows")
            
            for row in row_elements:
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells:  # Skip header row
                    row_data = []
                    for cell in cells:
                        value = self._extract_cell_value(cell)
                        row_data.append(value)
                    
                    if len(row_data) == len(headers):  # Only add rows that match header length
                        rows.append(row_data)
                    else:
                        logging.warning(f"Row data length ({len(row_data)}) doesn't match headers length ({len(headers)})")
        except NoSuchElementException:
            logging.warning("No data rows found in table")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=headers)
        logging.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
        return df
    
    def scrape_country_chart(self, country_code: str, data_type: str = "daily") -> Optional[pd.DataFrame]:
        """Scrape chart data for a specific country."""
        if not self.use_selenium or not self.driver:
            logging.error("Selenium WebDriver not initialized")
            return None
        
        url = self._get_url_for_country(country_code, data_type)
        retries = 0
        
        while retries < RETRY_COUNT:
            try:
                logging.info(f"Loading URL: {url}")
                self.driver.get(url)
                
                # Wait for page to load
                if not self._wait_for_page_load():
                    logging.error("Page failed to load completely")
                    retries += 1
                    self._random_sleep(2.0, 4.0)  # Longer delay between retries
                    continue
                
                # Save page source for debugging
                with open(f"debug_{country_code}_{data_type}.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logging.info(f"Saved page source to debug_{country_code}_{data_type}.html")
                
                # Wait for table
                wait = WebDriverWait(self.driver, WAIT_TIME)
                table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                
                # Extract table data
                df = self._extract_table_data(table)
                
                if df.empty:
                    logging.warning("No data found in table")
                    retries += 1
                    self._random_sleep(2.0, 4.0)
                    continue
                
                # Add metadata
                df['country'] = country_code.upper()
                df['data_type'] = data_type
                
                # Clean up numeric columns
                for col in df.columns:
                    if col not in ['date', 'country', 'data_type', 'song_name', 'artist_name']:
                        df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')
                
                return df
                
            except TimeoutException:
                logging.error(f"Timeout waiting for table to load: {url}")
                retries += 1
                self._random_sleep(2.0, 4.0)
            except Exception as e:
                logging.error(f"Error scraping country chart {country_code}: {e}")
                retries += 1
                self._random_sleep(2.0, 4.0)
        
        return None
    
    def scrape_track_history(self, track_id: str, data_type: str = "weekly") -> Optional[pd.DataFrame]:
        """Scrape streaming history for a track."""
        if not self.use_selenium or not self.driver:
            logging.error("Selenium WebDriver not initialized")
            return None
        
        url = self._get_url_for_track(track_id)
        retries = 0
        
        while retries < RETRY_COUNT:
            try:
                logging.info(f"Loading URL: {url}")
                self.driver.get(url)
                
                # Wait for page to load
                if not self._wait_for_page_load():
                    logging.error("Page failed to load completely")
                    retries += 1
                    self._random_sleep(2.0, 4.0)  # Longer delay between retries
                    continue
                
                # Save page source for debugging
                with open(f"debug_{track_id}.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logging.info(f"Saved page source to debug_{track_id}.html")
                
                # Switch to the desired view
                if data_type == "daily":
                    # Try to find and click the daily button
                    try:
                        daily_button = self.driver.find_element(By.ID, "daily")
                        if daily_button:
                            daily_button.click()
                            self._random_sleep(2.0, 3.0)
                    except:
                        logging.warning("Could not find daily view button")
                
                # Wait for table after view switch
                wait = WebDriverWait(self.driver, WAIT_TIME)
                table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                
                # Extract track info
                try:
                    title_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                    title = title_element.text.strip()
                    artist_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1 + p")))
                    artist = artist_element.text.strip()
                    logging.info(f"Found track info - Title: {title}, Artist: {artist}")
                except Exception as e:
                    logging.warning(f"Could not find track title or artist: {e}")
                    title = "Unknown"
                    artist = "Unknown"
                
                # Extract table data
                df = self._extract_table_data(table)
                
                if df.empty:
                    logging.warning("No data found in table")
                    retries += 1
                    self._random_sleep(2.0, 4.0)
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
                self._random_sleep(2.0, 4.0)
            except Exception as e:
                logging.error(f"Error scraping track {track_id}: {e}")
                retries += 1
                self._random_sleep(2.0, 4.0)
        
        return None
    
    def __del__(self):
        """Clean up Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.warning(f"Error closing WebDriver: {e}") 