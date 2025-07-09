"""Module for scraping Spotify chart data from KWORB."""
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import platform
import os
import shutil
from fake_useragent import UserAgent

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
        """Initialize Selenium WebDriver with anti-detection measures."""
        try:
            # Initialize fake user agent
            ua = UserAgent()
            
            options = webdriver.ChromeOptions()
            options.add_argument('--headless=new')  # Use new headless mode
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            
            # Anti-bot detection measures
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Set random user agent
            options.add_argument(f'user-agent={ua.random}')
            
            # Add language and platform
            options.add_argument('--lang=en-US,en;q=0.9')
            if platform.system() == 'Darwin':
                options.add_argument('--platform=MacIntel')
            else:
                options.add_argument('--platform=Linux x86_64')
            
            # Add additional headers
            options.add_argument('--accept-language=en-US,en;q=0.9')
            options.add_argument('--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
            
            # Add window size and position randomization
            width = random.randint(1024, 1920)
            height = random.randint(768, 1080)
            options.add_argument(f'--window-size={width},{height}')
            
            # Add other anti-detection measures
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2,  # Disable images for faster loading
                    'plugins': 2,  # Disable plugins
                    'geolocation': 2,  # Disable geolocation
                    'notifications': 2  # Disable notifications
                },
                'profile.password_manager_enabled': False,
                'credentials_enable_service': False,
                'profile.managed_default_content_settings.javascript': 1,  # Enable JavaScript
                'profile.managed_default_content_settings.cookies': 1  # Enable cookies
            }
            options.add_experimental_option('prefs', prefs)
            
            # Platform specific configurations
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
            
            # Execute CDP commands to modify navigator properties
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": ua.random,
                "platform": "MacIntel" if platform.system() == 'Darwin' else "Linux x86_64",
                "acceptLanguage": "en-US,en;q=0.9"
            })
            
            # Add webdriver detection evasion
            self.driver.execute_script("""
                // Overwrite the 'navigator.webdriver' property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Add missing properties that regular browsers have
                window.chrome = {
                    runtime: {}
                };
                
                // Add language and platform info
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            self.wait = WebDriverWait(self.driver, 10)  # Create a WebDriverWait instance
            logger.info("Selenium WebDriver initialized successfully with anti-detection measures")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {e}")
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
            
            # Random mouse movements (in headless mode, this is just for bot detection evasion)
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
            logger.warning(f"Error during human behavior simulation: {e}")

    def _check_element_exists(self, by, value, timeout=5) -> bool:
        """Check if an element exists on the page."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    def _find_element_safely(self, by, value, timeout=5, check_visibility=True):
        """Find an element with proper waiting and error handling."""
        try:
            if check_visibility:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((by, value))
                )
            else:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            return element
        except TimeoutException:
            logger.warning(f"Element not found: {value}")
            return None

    def _find_elements_safely(self, by, value, timeout=5, check_visibility=True):
        """Find elements with proper waiting and error handling."""
        try:
            if check_visibility:
                WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((by, value))
                )
            else:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            return self.driver.find_elements(by, value)
        except TimeoutException:
            logger.warning(f"No elements found: {value}")
            return []

    def _click_safely(self, element, timeout=5):
        """Click an element with proper waiting and error handling."""
        if not element:
            return False
        
        try:
            # Scroll into view with random offset
            offset = random.randint(-100, 100)
            self.driver.execute_script(f"arguments[0].scrollIntoView(true); window.scrollBy(0, {offset});", element)
            self._random_sleep(0.5, 1.5)
            
            # Wait for element to be clickable
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.ID, element.get_attribute("id")))
            )
            
            # Add random delay before clicking
            self._random_sleep(0.2, 0.8)
            
            # Try different click methods
            try:
                # Move mouse to element with random offset
                actions = ActionChains(self.driver)
                x_offset = random.randint(-10, 10)
                y_offset = random.randint(-10, 10)
                actions.move_to_element_with_offset(element, x_offset, y_offset).perform()
                self._random_sleep(0.1, 0.3)
                
                element.click()
            except:
                self.driver.execute_script("arguments[0].click();", element)
            
            # Add random delay after clicking
            self._random_sleep(0.3, 1.0)
            
            return True
        except Exception as e:
            logger.warning(f"Failed to click element: {e}")
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

    def _extract_track_info(self) -> dict:
        """Extract track name and artist from the page."""
        try:
            # Try to find track info in the subcontainer div
            track_info = self.driver.execute_script("""
                // Try to find track info in the subcontainer div
                function findTrackInfo() {
                    // Look for the subcontainer div
                    var subcontainer = document.querySelector('div.subcontainer');
                    if (subcontainer) {
                        var text = subcontainer.textContent;
                        
                        // Extract title
                        var titleMatch = text.match(/Title:\\s*([^\\n]+)/);
                        var songName = titleMatch ? titleMatch[1].trim() : null;
                        
                        // Extract artist
                        var artistMatch = text.match(/Artist:\\s*([^\\n]+)/);
                        var artistName = artistMatch ? artistMatch[1].trim() : null;
                        
                        // Clean up artist name (remove any trailing links or text)
                        if (artistName) {
                            artistName = artistName.split('Show:')[0].trim();
                        }
                        
                        if (songName && artistName) {
                            return {
                                song: songName,
                                artist: artistName
                            };
                        }
                    }
                    return null;
                }
                return findTrackInfo();
            """)
            
            if track_info:
                logger.info(f"Found track info in subcontainer: {track_info}")
                return {
                    "song_name": track_info["song"],
                    "artist_name": track_info["artist"]
                }
            
            # Fallback: Try to find track info in the page title
            title = self.driver.title
            if " by " in title and " - " in title:
                # Format is usually "Song Name by Artist - Spotify Charts History"
                track_part = title.split(" - ")[0]
                song_name = track_part.split(" by ")[0].strip()
                artist_name = track_part.split(" by ")[1].strip()
                logger.info(f"Found track info in title: {song_name} by {artist_name}")
                return {"song_name": song_name, "artist_name": artist_name}
            
            # Fallback: Try to find track info in any text that matches the pattern
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            for line in page_text.split('\n'):
                if 'Title:' in line:
                    song_name = line.replace('Title:', '').strip()
                    logger.info(f"Found song name in text: {song_name}")
                    continue
                if 'Artist:' in line:
                    artist_name = line.replace('Artist:', '').strip()
                    if 'Show:' in artist_name:
                        artist_name = artist_name.split('Show:')[0].strip()
                    logger.info(f"Found artist name in text: {artist_name}")
                    if song_name and artist_name:
                        return {"song_name": song_name, "artist_name": artist_name}
            
            logger.warning("Could not find track info in page")
            return {"song_name": "Unknown", "artist_name": "Unknown"}
            
        except Exception as e:
            logger.warning(f"Error extracting track info: {e}")
            return {"song_name": "Unknown", "artist_name": "Unknown"}

    def scrape_track_history(self, track_id: str) -> pd.DataFrame:
        """
        Scrape track streaming history from KWORB.
        
        Args:
            track_id: Spotify track ID
            
        Returns:
            DataFrame with track streaming history (Date, Global columns)
        """
        # Validate track ID
        if not track_id or not isinstance(track_id, str):
            logger.error("Invalid track ID provided")
            return pd.DataFrame()
        
        # Clean track ID (remove any query parameters or extra characters)
        track_id = track_id.split('?')[0].strip()
        
        # Remove any URL parts if they were accidentally included
        if "spotify.com/track/" in track_id:
            track_id = track_id.split("track/")[-1].split("?")[0].split("/")[0]
        elif "spotify:track:" in track_id:
            track_id = track_id.split("spotify:track:")[-1].split("?")[0]
        elif "kworb.net/spotify/track/" in track_id:
            track_id = track_id.split("track/")[-1].split(".")[0]
        
        # Validate track ID format (should be a string of alphanumeric characters)
        if not track_id.replace("-", "").isalnum():
            logger.error(f"Invalid track ID format: {track_id}")
            return pd.DataFrame()
        
        url = f"https://kworb.net/spotify/track/{track_id}.html"
        logger.info(f"Scraping track history from: {url}")
        
        try:
            # Add random delay before loading page
            self._random_sleep(1.0, 3.0)
            
            # Load the page
            self.driver.get(url)
            logger.info("Initial page load complete")
            
            # Extract track info
            track_info = self._extract_track_info()
            logger.info(f"Found track info: {track_info}")
            
            # Simulate human behavior
            self._simulate_human_behavior()
            
            # Wait for page to be fully loaded with random delay
            self._random_sleep(3.0, 5.0)
            
            # Check if page loaded successfully
            if "404" in self.driver.title or "Not Found" in self.driver.title:
                logger.error(f"Page not found for track ID: {track_id}")
                return pd.DataFrame()
            
            # Check if we're being blocked
            if "Access Denied" in self.driver.page_source or "Forbidden" in self.driver.page_source:
                logger.error("Access to the page was denied. The website might be blocking our requests.")
                # Reinitialize the driver with new user agent
                self._init_selenium()
                return pd.DataFrame()
            
            # Save initial page source for debugging
            with open(f"debug_{track_id}_initial.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.info(f"Saved initial page source to debug_{track_id}_initial.html")
            
            # Execute JavaScript to ensure page is fully loaded and trigger weekly view
            self.driver.execute_script("""
                // Wait for document to be ready
                if (document.readyState !== 'complete') {
                    return false;
                }
                
                // Try to find and click the weekly button
                var weeklyBtn = document.getElementById('weekly');
                if (weeklyBtn) {
                    weeklyBtn.click();
                }
                
                // Try to find and click the streams button
                var streamsBtn = document.getElementById('streams');
                if (streamsBtn) {
                    streamsBtn.click();
                }
                
                return true;
            """)
            
            logger.info("JavaScript execution complete")
            self._random_sleep(2.0, 4.0)
            
            # Save page source after JavaScript execution
            with open(f"debug_{track_id}_after_js.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.info(f"Saved post-JavaScript page source to debug_{track_id}_after_js.html")
            
            # Try to execute JavaScript to get table HTML directly
            table_html = self.driver.execute_script("""
                var weeklyDiv = document.querySelector('div.weekly');
                if (weeklyDiv) {
                    var table = weeklyDiv.querySelector('table');
                    if (table) {
                        return table.outerHTML;
                    }
                }
                return document.querySelector('table') ? document.querySelector('table').outerHTML : null;
            """)
            
            if table_html:
                logger.info("Found table via JavaScript")
                with open(f"debug_{track_id}_table.html", "w", encoding="utf-8") as f:
                    f.write(table_html)
                logger.info(f"Saved table HTML to debug_{track_id}_table.html")
            else:
                logger.warning("No table found via JavaScript")
            
            # Try multiple strategies to find the streaming data
            table = None
            
            # Strategy 1: Try to find table directly
            table_locators = [
                (By.CSS_SELECTOR, "div.weekly table"),  # Weekly view table
                (By.CSS_SELECTOR, "div.weekly > table"),  # Direct child table
                (By.XPATH, "//div[contains(@class, 'weekly')]/table"),  # Another way to find weekly table
                (By.XPATH, "//table[.//tr[1][contains(., 'Date') and contains(., 'Global')]]"),  # Table with Date and Global in first row
                (By.XPATH, "//table[.//th[1][contains(text(), 'Date')] and .//th[2][contains(text(), 'Global')]]"),  # More specific header structure
                (By.CSS_SELECTOR, "table"),  # Any table
                (By.XPATH, "//table[contains(@class, 'weekly') or contains(@class, 'streams')]")  # Tables with specific classes
            ]
            
            for by, value in table_locators:
                logger.info(f"Trying to find table with: {by} = {value}")
                table = self._find_element_safely(by, value)
                if table:
                    logger.info(f"Found table with: {by} = {value}")
                    break
                else:
                    logger.warning(f"Table not found with: {by} = {value}")
            
            if not table:
                logger.warning("Could not find streaming data table after multiple attempts")
                return pd.DataFrame()
            
            # Process the table data
            data = {
                'date': []
            }
            
            # Get headers first to find correct column indices
            headers = [cell.text.strip() for cell in table.find_elements(By.TAG_NAME, "th")]
            logger.info(f"Found table headers: {headers}")
            
            # Initialize data dictionary with all columns
            for header in headers:
                if header != 'Date':  # Date is already handled as 'date'
                    data[header] = []
            
            # Find date column index
            try:
                date_idx = headers.index('Date')
            except ValueError:
                date_idx = 0  # Assume first column is date if not labeled
                logger.warning("Date column not found in headers, using first column")
            
            # Get all rows
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
            logger.info(f"Found {len(rows)} data rows")
            
            # Process each row with retry logic for stale elements
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < len(headers):
                        logger.warning(f"Row has fewer cells ({len(cells)}) than headers ({len(headers)}), skipping")
                        continue
                    
                    # Get date value
                    date_value = cells[date_idx].text.strip()
                    data['date'].append(date_value)
                    
                    # Get values for all other columns
                    for i, header in enumerate(headers):
                        if header != 'Date':
                            value = cells[i].text.strip()
                            data[header].append(self._parse_number(value))
                
                except StaleElementReferenceException:
                    logger.warning("Encountered stale element, skipping row")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing row: {e}")
                    continue
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            if df.empty:
                logger.warning("No data was extracted from the table")
                return df
            
            # Add track info to the DataFrame
            df['song_name'] = track_info['song_name']
            df['artist_name'] = track_info['artist_name']
            
            # Process the data
            df['date'] = df['date'].apply(self._parse_date)
            
            # Handle special rows (Total, Peak)
            special_rows = ['Total', 'Peak']
            total_peak_df = df[df['date'].isin(special_rows)]
            regular_df = df[~df['date'].isin(special_rows)].sort_values('date', ascending=False)
            
            # Combine the dataframes
            final_df = pd.concat([total_peak_df, regular_df], ignore_index=True)
            
            # Reorder columns to put song and artist first
            cols = ['song_name', 'artist_name', 'date'] + [col for col in final_df.columns if col not in ['song_name', 'artist_name', 'date']]
            final_df = final_df[cols]
            
            logger.info(f"Successfully extracted data with {len(final_df)} rows")
            return final_df
            
        except Exception as e:
            logger.error(f"Failed to scrape track history: {e}")
            return pd.DataFrame()  # Return empty DataFrame instead of raising error
    
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