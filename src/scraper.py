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
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'user-agent={UserAgent().random}')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(WAIT_TIME)
        except Exception as e:
            logging.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def _get_url_for_track(self, track_id: str) -> str:
        """Get the URL for a track's chart data."""
        return f"{KWORB_BASE_URL}/track/{track_id}.html"
    
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
            
            # Wait for any table to be present
            WebDriverWait(self.driver, WAIT_TIME).until(
                presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Wait a bit more for JavaScript to execute
            time.sleep(2)
            return True
        except Exception as e:
            logging.error(f"Error waiting for page load: {e}")
            return False
    
    def _switch_view(self, view_type: str) -> bool:
        """Switch between daily and weekly views."""
        try:
            # Wait for the button to be present and visible
            wait = WebDriverWait(self.driver, WAIT_TIME)
            button = wait.until(
                visibility_of_element_located((By.ID, view_type))
            )
            
            if button:
                logging.info(f"Found {view_type} button, clicking...")
                # Try JavaScript click first
                try:
                    self.driver.execute_script("arguments[0].click();", button)
                except:
                    # Fallback to regular click
                    button.click()
                
                # Wait for view to update
                time.sleep(3)
                
                # Verify the view switched by checking button state
                try:
                    button = self.driver.find_element(By.ID, view_type)
                    if "bold" in button.get_attribute("style"):
                        logging.info(f"Successfully switched to {view_type} view")
                        return True
                except:
                    pass
                
                logging.warning(f"Could not verify {view_type} view switch")
                return False
            
            logging.warning(f"Button for {view_type} view not found")
            return False
            
        except Exception as e:
            logging.error(f"Error switching to {view_type} view: {e}")
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
                    continue
                
                # Save page source for debugging
                with open(f"debug_{track_id}.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logging.info(f"Saved page source to debug_{track_id}.html")
                
                # Switch to the desired view
                if data_type == "daily":
                    if not self._switch_view("daily"):
                        logging.error("Failed to switch to daily view")
                        retries += 1
                        continue
                else:
                    if not self._switch_view("weekly"):
                        logging.error("Failed to switch to weekly view")
                        retries += 1
                        continue
                
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