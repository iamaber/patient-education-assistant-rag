import json
import time
import os
import random
import logging
from typing import List, Tuple, Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration constants
BASE_URL = "https://medex.com.bd"
BRANDS_URL = f"{BASE_URL}/brands?page="
DEFAULT_CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
OUTPUT_DIR = "data/drug_db"
OUTPUT_FILE = "medex_data.json"
MIN_DELAY = 2
MAX_DELAY = 5
PAGE_LOAD_TIMEOUT = 15
ELEMENT_CLICK_TIMEOUT = 10
MAX_CONSECUTIVE_ERRORS = 3
LONG_BREAK_PROBABILITY = 0.1
LONG_BREAK_DURATION = (15, 30)


class MedexScraper:
    """A web scraper for collecting medicine data from Medex website."""

    def __init__(self, chromedriver_path: str = DEFAULT_CHROMEDRIVER_PATH):
        """
        Initialize the MedexScraper.

        Args:
            chromedriver_path: Path to the ChromeDriver executable
        """
        self.chromedriver_path = chromedriver_path
        self.user_agent = UserAgent()
        self.medicines_data: List[Dict[str, Any]] = []
        self.driver: Optional[webdriver.Chrome] = None

    def _get_random_delay(
        self, min_delay: float = MIN_DELAY, max_delay: float = MAX_DELAY
    ) -> float:
        """Generate a random delay between requests."""
        return random.uniform(min_delay, max_delay)

    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome driver with anti-detection measures."""
        options = webdriver.ChromeOptions()

        # Set random user agent
        options.add_argument(f"user-agent={self.user_agent.random}")

        # Additional anti-detection options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Set window size to a common resolution
        options.add_argument("--window-size=1920,1080")

        # Initialize the driver
        service = Service(executable_path=self.chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)

        # Execute script to remove webdriver property
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        return driver

    def _handle_security_check(self) -> bool:
        """
        Handle security check by pausing and allowing manual intervention.

        Returns:
            True if security check was successfully handled, False otherwise
        """
        logger.warning("SECURITY CHECK DETECTED!")
        logger.warning("Please complete the security check in the browser window.")
        logger.warning(
            "After completing the check, press Enter in this console to continue..."
        )

        # Wait for user to complete the security check
        input("Press Enter after completing the security check...")

        # Wait a moment for the page to load after the check
        time.sleep(2)

        # Check if we're still on a security check page
        if self.driver:
            page_source = self.driver.page_source.lower()
            if "security check" in page_source or "captcha" in page_source:
                logger.error(
                    "Security check still detected. Please try again or consider using a different IP address."
                )
                return False

        return True

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """
        Clean and normalize text content.

        Args:
            text: Text to clean

        Returns:
            Cleaned text or None if input was None/empty
        """
        if text:
            return " ".join(text.strip().split())
        return None

    def _find_section_content(
        self, soup: BeautifulSoup, heading_text: str
    ) -> Optional[str]:
        """
        Find content under a specific heading in the page structure.

        Args:
            soup: BeautifulSoup object of the page
            heading_text: Text to search for in headings

        Returns:
            Content text or None if not found
        """
        # Find the heading element containing text
        heading = soup.find(
            ["h3", "h4", "h5"], string=lambda t: t and heading_text in t
        )

        if heading:
            parent_div = heading.parent
            content_div = parent_div.find_next_sibling()

            if content_div and "ac-body" in content_div.get("class", []):
                return self._clean_text(content_div.get_text(separator=" ", strip=True))
        return None

    def _wait_and_click(
        self, by: By, value: str, timeout: int = ELEMENT_CLICK_TIMEOUT
    ) -> bool:
        """
        Wait for element to be clickable and click it.

        Args:
            by: Selenium By selector type
            value: Selector value
            timeout: Maximum time to wait for element

        Returns:
            True if element was clicked successfully, False otherwise
        """
        try:
            if not self.driver:
                return False

            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            return True
        except TimeoutException:
            logger.warning(f"Element not clickable: {by}={value}")
            return False

    def _check_for_security_page(self) -> bool:
        """
        Check if current page is a security check page.

        Returns:
            True if security check is detected, False otherwise
        """
        if not self.driver:
            return False

        page_source = self.driver.page_source.lower()
        return "security check" in page_source or "captcha" in page_source

    def _wait_for_page_load(
        self, selector: Tuple[By, str], timeout: int = PAGE_LOAD_TIMEOUT
    ) -> bool:
        """
        Wait for a specific element to appear on the page.

        Args:
            selector: Tuple of (By, selector_value) to wait for
            timeout: Maximum time to wait

        Returns:
            True if element appeared, False on timeout
        """
        try:
            if not self.driver:
                return False

            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(selector)
            )
            return True
        except TimeoutException:
            return False

    def _extract_medicine_details(self, page_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract detailed information about a medicine from its page.

        Args:
            page_url: URL of the medicine page

        Returns:
            Dictionary with medicine details or None if extraction failed
        """
        try:
            if not self.driver:
                return None

            # Add random delay before making request
            time.sleep(self._get_random_delay())

            self.driver.get(page_url)

            # Check for security check
            if self._check_for_security_page():
                if not self._handle_security_check():
                    return None

            # Wait for page to load
            page_heading_selector = (By.CSS_SELECTOR, "h1.page-heading-1-l")
            if not self._wait_for_page_load(page_heading_selector):
                # Check again for security check
                if self._check_for_security_page():
                    if not self._handle_security_check():
                        return None
                    else:
                        # Try waiting again after security check
                        if not self._wait_for_page_load(page_heading_selector):
                            logger.warning(
                                f"Timeout waiting for page to load: {page_url}"
                            )
                            return None

            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            medicine_item: Dict[str, Any] = {}

            # Brand name
            brand_name = soup.select_one("h1.page-heading-1-l")
            medicine_item["brand_name"] = (
                self._clean_text(brand_name.text) if brand_name else None
            )

            # Generic name
            generic_info = soup.select_one('div[title="Generic Name"] a')
            medicine_item["generic_name"] = (
                self._clean_text(generic_info.text) if generic_info else None
            )

            # Manufacturer Name
            manufacturer_info = soup.find("div", title="Manufactured by")
            if manufacturer_info:
                manufacturer_name_tag = manufacturer_info.find("a")
                medicine_item["manufacturer_name"] = (
                    self._clean_text(manufacturer_name_tag.text)
                    if manufacturer_name_tag
                    else None
                )
            else:
                medicine_item["manufacturer_name"] = None

            # Dosage Form
            dosage_form_tag = soup.select_one(
                'h1.page-heading-1-l small[title="Dosage Form"]'
            )
            medicine_item["dosage_form"] = (
                self._clean_text(dosage_form_tag.text) if dosage_form_tag else None
            )

            # Strength
            strength = soup.select_one('div[title="Strength"]')
            medicine_item["strength"] = (
                self._clean_text(strength.text) if strength else None
            )

            # Unit Price
            price_info = soup.find("div", class_="package-container")
            if price_info:
                price_span = price_info.find_all("span")
                if len(price_span) > 1:
                    medicine_item["unit_price"] = self._clean_text(price_span[1].text)
                else:
                    medicine_item["unit_price"] = None
            else:
                medicine_item["unit_price"] = None

            # Medical information sections
            medicine_item["indications"] = self._find_section_content(
                soup, "Indications"
            )
            medicine_item["pharmacology"] = self._find_section_content(
                soup, "Pharmacology"
            )
            medicine_item["dosage_and_administration"] = self._find_section_content(
                soup, "Dosage & Administration"
            )
            medicine_item["contraindications"] = self._find_section_content(
                soup, "Contraindications"
            )
            medicine_item["side_effects"] = self._find_section_content(
                soup, "Side Effects"
            )
            medicine_item["pregnancy_and_lactation"] = self._find_section_content(
                soup, "Pregnancy & Lactation"
            )
            medicine_item["precautions_and_warnings"] = self._find_section_content(
                soup, "Precautions & Warnings"
            )
            medicine_item["overdose_effects"] = self._find_section_content(
                soup, "Overdose Effects"
            )

            return medicine_item

        except Exception as e:
            logger.error(f"Error fetching {page_url}: {e}")
            return None

    def _scrape_brand_page(self, page_number: int) -> Tuple[List[str], bool]:
        """
        Scrape a page of medicine brands to get individual medicine URLs.

        Args:
            page_number: Page number to scrape

        Returns:
            Tuple of (list of medicine URLs, has_next_page)
        """
        url = f"{BRANDS_URL}{page_number}"

        # Add random delay before making request
        time.sleep(self._get_random_delay())

        try:
            if not self.driver:
                return [], False

            self.driver.get(url)

            # Check for security check
            if self._check_for_security_page():
                if not self._handle_security_check():
                    return [], False

            # Wait for page to load
            medicine_links_selector = (By.CSS_SELECTOR, "a.hoverable-block")
            if not self._wait_for_page_load(medicine_links_selector):
                # Check again for security check
                if self._check_for_security_page():
                    if not self._handle_security_check():
                        return [], False
                    else:
                        # Try waiting again after security check
                        if not self._wait_for_page_load(medicine_links_selector):
                            logger.warning(f"Timeout waiting for page to load: {url}")
                            return [], False

            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            medicine_links = soup.select("a.hoverable-block")
            links = [link.get("href") for link in medicine_links if link.get("href")]

            next_page_link = soup.select_one('a.page-link[rel="next"]')
            has_next_page = next_page_link is not None

            return links, has_next_page

        except TimeoutException:
            logger.error(f"Timeout while loading page {page_number}")
            return [], False
        except Exception as e:
            logger.error(f"Error scraping page {page_number}: {e}")
            return [], False

    def scrape_medicines(
        self, start_page: int = 1, max_pages: Optional[int] = None
    ) -> None:
        """
        Main method to crawl and scrape medicine data.

        Args:
            start_page: Page number to start scraping from
            max_pages: Maximum number of pages to scrape (None for all)
        """
        self.driver = self._setup_driver()

        try:
            # First, visit the base URL to establish session
            self.driver.get(BASE_URL)
            logger.info(f"Established session with {BASE_URL}")
            time.sleep(3)  # Allow time for page to load

            # Check for initial security check
            if self._check_for_security_page():
                if not self._handle_security_check():
                    logger.error("Initial security check failed. Exiting.")
                    return

            page_number = start_page
            consecutive_errors = 0

            while True:
                try:
                    logger.info(f"Scraping page {page_number}...")
                    medicine_urls, has_next_page = self._scrape_brand_page(page_number)

                    if not medicine_urls:
                        consecutive_errors += 1
                        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                            logger.error(
                                f"Too many consecutive errors ({MAX_CONSECUTIVE_ERRORS}). Stopping."
                            )
                            break
                        logger.warning(
                            f"No medicine URLs found on page {page_number}. Trying next page."
                        )
                        page_number += 1
                        continue

                    consecutive_errors = (
                        0  # Reset error counter on successful page scrape
                    )

                    # Randomize the order of processing URLs
                    random.shuffle(medicine_urls)

                    for url in medicine_urls:
                        details = self._extract_medicine_details(url)
                        if details:
                            self.medicines_data.append(details)
                            logger.info(
                                f"Scraped medicine: {details.get('brand_name', 'Unknown')}"
                            )
                        else:
                            logger.warning(f"Failed to scrape details from: {url}")

                    if not has_next_page or (max_pages and page_number >= max_pages):
                        logger.info(
                            "Finished crawling all available pages or reached the page limit."
                        )
                        break

                    page_number += 1

                    # Occasionally take a longer break
                    if random.random() < LONG_BREAK_PROBABILITY:
                        longer_break = random.uniform(*LONG_BREAK_DURATION)
                        logger.info(
                            f"Taking a longer break for {longer_break:.2f} seconds..."
                        )
                        time.sleep(longer_break)

                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Error on page {page_number}: {e}")
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        logger.error(
                            f"Too many consecutive errors ({MAX_CONSECUTIVE_ERRORS}). Stopping."
                        )
                        break
                    page_number += 1
                    continue

        finally:
            if self.driver:
                self.driver.quit()

    def save_data(self) -> None:
        """Save the scraped data to a JSON file."""
        # Create the output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Save the scraped data to a JSON file
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.medicines_data, f, ensure_ascii=False, indent=4)

        logger.info(
            f"Successfully scraped {len(self.medicines_data)} medicine brands and saved to {output_path}"
        )


def main() -> None:
    """Main function to run the scraper."""
    scraper = MedexScraper()
    scraper.scrape_medicines(max_pages=844)
    scraper.save_data()


if __name__ == "__main__":
    main()
