"""Module for scraping Spotify chart data from KWORB."""
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import platform
import os
import shutil
import time

logger = logging.getLogger(__name__)

class ScrapingError(Exception):
    """Custom exception for scraping errors."""
    pass

class ChartScraper:
    """Scraper for KWORB Spotify charts."""
    
    def __init__(self, use_selenium: bool = True):
        """Initialize the scraper."""
        self.use_selenium = use_selenium
        if use_selenium:
            self._init_selenium()
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver."""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-extensions')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Add specific configurations for different environments
            if platform.system() == 'Darwin':  # macOS
                if platform.machine() == 'arm64':
                    options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
                service = Service()
            else:  # Linux (Streamlit Cloud)
                if os.path.exists('/usr/bin/chromium'):
                    options.binary_location = '/usr/bin/chromium'
                    chrome_driver_path = '/usr/bin/chromedriver'
                    if os.path.exists(chrome_driver_path):
                        service = Service(chrome_driver_path)
                    else:
                        chrome_driver_path = shutil.which('chromedriver')
                        if chrome_driver_path:
                            service = Service(chrome_driver_path)
                        else:
                            service = Service(ChromeDriverManager().install())
                else:
                    service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            raise

    def _wait_for_element(self, by, value, timeout=10, condition=EC.presence_of_element_located):
        """Wait for an element with explicit wait and retry logic."""
        start_time = time.time()
        last_exception = None
        
        while time.time() - start_time < timeout:
            try:
                element = WebDriverWait(self.driver, 2).until(condition((by, value)))
                return element
            except (TimeoutException, StaleElementReferenceException) as e:
                last_exception = e
                time.sleep(0.5)
                continue
        
        if last_exception:
            logger.warning(f"Element not found after {timeout} seconds: {value}")
            return None
        return None

    def _wait_for_elements(self, by, value, timeout=10, condition=EC.presence_of_all_elements_located):
        """Wait for elements with explicit wait and retry logic."""
        element = self._wait_for_element(by, value, timeout, condition)
        if element:
            return self.driver.find_elements(by, value)
        return []

    def _safe_click(self, element, timeout=10):
        """Safely click an element with retry logic."""
        if not element:
            return False
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                
                # Wait for element to be clickable
                WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.ID, element.get_attribute("id")))
                )
                
                # Try clicking
                element.click()
                return True
            except Exception as e:
                logger.warning(f"Click attempt failed: {e}")
                time.sleep(0.5)
                continue
        
        return False
    
    def _parse_number(self, value: str) -> Optional[int]:
        """Parse number from string, handling commas and dashes."""
        try:
            if value == '--' or not value:
                return None
            return int(value.replace(',', ''))
        except (ValueError, AttributeError):
            return None
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date string to YYYY/MM/DD format."""
        try:
            date_obj = datetime.strptime(date_str, '%Y/%m/%d')
            return date_obj.strftime('%Y/%m/%d')
        except ValueError:
            return date_str

    def scrape_track_history(self, track_id: str) -> pd.DataFrame:
        """
        Scrape track streaming history from KWORB.
        
        Args:
            track_id: Spotify track ID
            
        Returns:
            DataFrame with track streaming history (Date, Global, US columns)
        """
        url = f"https://kworb.net/spotify/track/{track_id}.html"
        logger.info(f"Scraping track history from: {url}")
        
        try:
            # Load the page and wait for it to be ready
            self.driver.get(url)
            time.sleep(3)  # Initial page load wait
            
            # Try multiple strategies to find the streaming data
            
            # Strategy 1: Look for table directly
            table = self._wait_for_element(
                By.CSS_SELECTOR, 
                "table:has(th:contains('Date')):has(th:contains('Global'))",
                timeout=5
            )
            
            # Strategy 2: Try clicking "Streams" link if table not found
            if not table:
                logger.info("Table not found directly, trying Streams link...")
                streams_link = self._wait_for_element(
                    By.XPATH,
                    "//a[contains(text(), 'Streams')] | //a[.='Streams']",
                    timeout=5
                )
                
                if streams_link and self._safe_click(streams_link):
                    logger.info("Clicked Streams link, waiting for table...")
                    time.sleep(2)
                    table = self._wait_for_element(
                        By.CSS_SELECTOR,
                        "table:has(th:contains('Date')):has(th:contains('Global'))",
                        timeout=5
                    )
            
            # Strategy 3: Look for any table with streaming data
            if not table:
                logger.info("Trying to find any table with streaming data...")
                tables = self._wait_for_elements(By.TAG_NAME, "table", timeout=5)
                for potential_table in tables:
                    headers = [cell.text.strip() for cell in potential_table.find_elements(By.TAG_NAME, "th")]
                    if "Date" in headers and "Global" in headers:
                        table = potential_table
                        break
            
            if not table:
                raise ScrapingError("Could not find streaming data table after multiple attempts")
            
            # Process the table data
            data = {
                'date': [],
                'Global': [],
                'US': []
            }
            
            # Get headers first to find correct column indices
            headers = [cell.text.strip() for cell in table.find_elements(By.TAG_NAME, "th")]
            try:
                date_idx = headers.index('Date')
                global_idx = headers.index('Global')
                us_idx = headers.index('US')
            except ValueError:
                raise ScrapingError("Required columns (Date, Global, US) not found in table")
            
            # Get all rows
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
            
            # Process each row with retry logic for stale elements
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if not cells:
                        continue
                    
                    # Get values with explicit waits
                    date_value = cells[date_idx].text.strip()
                    global_value = cells[global_idx].text.strip()
                    us_value = cells[us_idx].text.strip()
                    
                    data['date'].append(date_value)
                    data['Global'].append(self._parse_number(global_value))
                    data['US'].append(self._parse_number(us_value))
                except StaleElementReferenceException:
                    logger.warning("Encountered stale element, skipping row")
                    continue
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Process the data
            df['date'] = df['date'].apply(self._parse_date)
            
            # Handle special rows
            total_peak_df = df[df['date'].isin(['Total', 'Peak'])]
            regular_df = df[~df['date'].isin(['Total', 'Peak'])].sort_values('date', ascending=False)
            
            # Combine the dataframes
            final_df = pd.concat([total_peak_df, regular_df], ignore_index=True)
            
            return final_df
            
        except Exception as e:
            logger.error(f"Failed to scrape track history: {e}")
            raise ScrapingError(f"Failed to scrape track history: {e}")
    
    def discover_available_weeks(self) -> List[datetime]:
        """Discover available chart weeks."""
        logger.info("Discovering available chart weeks...")
        url = "https://kworb.net/spotify/"
        
        try:
            self.driver.get(url)
            
            # Try to find the table with dates
            try:
                table = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
            except TimeoutException:
                logger.warning("Table element not found, proceeding with available content")
                table = None
            
            dates = []
            if table:
                # Find all date links
                date_links = table.find_elements(By.TAG_NAME, "a")
                for link in date_links:
                    try:
                        date_text = link.text.strip()
                        date_obj = datetime.strptime(date_text, '%Y/%m/%d')
                        dates.append(date_obj)
                    except ValueError:
                        continue
            
            if not dates:
                logger.warning("No dates found in the page")
                # Use current date as fallback
                current_date = datetime.now()
                logger.info(f"Using current date as fallback: {current_date}")
                dates = [current_date]
            
            logger.info(f"Discovered {len(dates)} available chart weeks")
            return sorted(dates)
            
        except Exception as e:
            logger.error(f"Failed to discover available weeks: {e}")
            raise ScrapingError(f"Failed to discover available weeks: {e}")
    
    def scrape_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        output_dir: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Scrape chart data for a date range.
        
        Args:
            start_date: Start date to scrape from
            end_date: End date to scrape to
            output_dir: Optional directory to save raw data files
            
        Returns:
            DataFrame with combined chart data
        """
        try:
            available_dates = self.discover_available_weeks()
            dates_to_scrape = [
                d for d in available_dates
                if start_date <= d <= end_date
            ]
            
            all_data = []
            for date in dates_to_scrape:
                date_str = date.strftime('%Y/%m/%d')
                url = f"https://kworb.net/spotify/weekly/{date_str}.html"
                
                try:
                    self.driver.get(url)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "table"))
                    )
                    
                    # Find the main data table
                    tables = self.driver.find_elements(By.TAG_NAME, "table")
                    if not tables:
                        logger.warning(f"No data tables found for date: {date_str}")
                        continue
                    
                    # Get column headers
                    headers = []
                    header_cells = tables[0].find_elements(By.TAG_NAME, "th")
                    for cell in header_cells:
                        headers.append(cell.text.strip())
                    
                    # Initialize data dictionary
                    data = {header: [] for header in headers}
                    data['chart_date'] = []  # Add date column
                    
                    # Get all rows
                    rows = tables[0].find_elements(By.TAG_NAME, "tr")
                    
                    for row in rows[1:]:  # Skip header row
                        cells = row.find_elements(By.TAG_NAME, "td")
                        data['chart_date'].append(date_str)
                        
                        for header, cell in zip(headers, cells):
                            value = cell.text.strip()
                            if header in ['Global', 'US', 'PH', 'GB', 'CA', 'ID', 'AU', 'MY', 'IE', 
                                        'SG', 'NO', 'AR', 'NZ', 'CL', 'AE', 'PE', 'PT', 'NL', 'SE', 'FI', 'CR']:
                                data[header].append(self._parse_number(value))
                            else:
                                data[header].append(value)
                    
                    # Create DataFrame for this date
                    df = pd.DataFrame(data)
                    all_data.append(df)
                    
                    # Save raw data if output directory provided
                    if output_dir:
                        output_dir = Path(output_dir)
                        output_dir.mkdir(parents=True, exist_ok=True)
                        output_file = output_dir / f"chart_{date_str}.csv"
                        df.to_csv(output_file, index=False)
                        logger.info(f"Saved raw data to: {output_file}")
                    
                except Exception as e:
                    logger.error(f"Failed to scrape data for {date_str}: {e}")
                    continue
            
            if not all_data:
                raise ScrapingError("No data scraped for the specified date range")
            
            # Combine all data
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Ensure consistent column order
            column_order = ['chart_date', 'Global', 'US', 'PH', 'GB', 'CA', 'ID', 'AU', 'MY', 'IE', 
                          'SG', 'NO', 'AR', 'NZ', 'CL', 'AE', 'PE', 'PT', 'NL', 'SE', 'FI', 'CR']
            
            # Add any missing columns with None values
            for col in column_order:
                if col not in combined_df.columns:
                    combined_df[col] = None
            
            # Reorder columns
            combined_df = combined_df[column_order]
            
            return combined_df
            
        except Exception as e:
            raise ScrapingError(f"Failed to scrape date range: {e}")
    
    def __del__(self):
        """Clean up Selenium WebDriver."""
        if hasattr(self, 'driver'):
            self.driver.quit() 