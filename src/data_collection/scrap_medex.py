import json
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

BASE_URL = "https://medex.com.bd"
BRANDS_URL = f"{BASE_URL}/brands?page="

# List of scraped medicine data
all_medicines = []

# Initialize a UserAgent object for rotating user agents
ua = UserAgent()


def get_random_delay(min_delay=2, max_delay=5):
    """Generate a random delay between requests"""
    return random.uniform(min_delay, max_delay)


def setup_driver():
    """Set up Chrome driver with anti-detection measures"""
    options = webdriver.ChromeOptions()

    # Set random user agent
    user_agent = ua.random
    options.add_argument(f"user-agent={user_agent}")

    # Run in headless mode (uncomment for production)
    # options.add_argument('--headless')

    # Additional anti-detection options
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Set window size to a common resolution
    options.add_argument("--window-size=1920,1080")

    # Initialize the driver
    service = Service(
        executable_path="/usr/local/bin/chromedriver"
    )  # Update with your chromedriver path
    driver = webdriver.Chrome(service=service, options=options)

    # Execute script to remove webdriver property
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


def handle_security_check(driver):
    """Handle security check by pausing and allowing manual intervention"""
    print("\n" + "=" * 50)
    print("SECURITY CHECK DETECTED!")
    print("Please complete the security check in the browser window.")
    print("After completing the check, press Enter in this console to continue...")
    print("=" * 50 + "\n")

    # Wait for user to complete the security check
    input("Press Enter after completing the security check...")

    # Wait a moment for the page to load after the check
    time.sleep(2)

    # Check if we're still on a security check page
    if (
        "security check" in driver.page_source.lower()
        or "captcha" in driver.page_source.lower()
    ):
        print(
            "Security check still detected. Please try again or consider using a different IP address."
        )
        return False

    return True


def clean_text(text):
    if text:
        return " ".join(text.strip().split())
    return None


def find_section_content(soup, heading_text):
    # find the heading element containing text
    heading = soup.find(["h3", "h4", "h5"], string=lambda t: t and heading_text in t)

    if heading:
        parent_div = heading.parent
        content_div = parent_div.find_next_sibling()

        if content_div and "ac-body" in content_div.get("class", []):
            return clean_text(content_div.get_text(separator=" ", strip=True))
    return None


def wait_and_click(driver, by, value, timeout=10):
    """Wait for element to be clickable and click it"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        return True
    except TimeoutException:
        print(f"Element not clickable: {by}={value}")
        return False


def extract_medicine_details(driver, page_url):
    try:
        # Add random delay before making request
        time.sleep(get_random_delay())

        driver.get(page_url)

        # Check for security check
        if (
            "security check" in driver.page_source.lower()
            or "captcha" in driver.page_source.lower()
        ):
            if not handle_security_check(driver):
                return None

        # Wait for page to load
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.page-heading-1-l"))
            )
        except TimeoutException:
            # Check again for security check
            if (
                "security check" in driver.page_source.lower()
                or "captcha" in driver.page_source.lower()
            ):
                if not handle_security_check(driver):
                    return None
                else:
                    # Try waiting again after security check
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "h1.page-heading-1-l")
                        )
                    )

        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        medicine_item = {}

        # brand name
        brand_name = soup.select_one("h1.page-heading-1-l")
        medicine_item["brand_name"] = (
            clean_text(brand_name.text) if brand_name else None
        )

        generic_info = soup.select_one('div[title="Generic Name"] a')
        if generic_info:
            medicine_item["generic_name"] = clean_text(generic_info.text)
        else:
            medicine_item["generic_name"] = None

        # Manufacturer Name
        manufacturer_info = soup.find("div", title="Manufactured by")
        if manufacturer_info:
            manufacturer_name_tag = manufacturer_info.find("a")
            medicine_item["manufacturer_name"] = (
                clean_text(manufacturer_name_tag.text)
                if manufacturer_name_tag
                else None
            )
        else:
            medicine_item["manufacturer_name"] = None

        # Dosage Form
        dosage_form_tag = soup.select_one(
            'h1.page-heading-1-l small[title="Dosage Form"]'
        )
        if dosage_form_tag:
            medicine_item["dosage_form"] = clean_text(dosage_form_tag.text)
        else:
            medicine_item["dosage_form"] = None

        # Strength
        strength = soup.select_one('div[title="Strength"]')
        medicine_item["strength"] = clean_text(strength.text) if strength else None

        # Unit Price
        price_info = soup.find("div", class_="package-container")
        if price_info:
            price_span = price_info.find_all("span")
            if len(price_span) > 1:
                medicine_item["unit_price"] = clean_text(price_span[1].text)
            else:
                medicine_item["unit_price"] = None
        else:
            medicine_item["unit_price"] = None

        medicine_item["indications"] = find_section_content(soup, "Indications")
        medicine_item["pharmacology"] = find_section_content(soup, "Pharmacology")
        medicine_item["dosage_and_administration"] = find_section_content(
            soup, "Dosage & Administration"
        )
        medicine_item["contraindications"] = find_section_content(
            soup, "Contraindications"
        )
        medicine_item["side_effects"] = find_section_content(soup, "Side Effects")
        medicine_item["pregnancy_and_lactation"] = find_section_content(
            soup, "Pregnancy & Lactation"
        )
        medicine_item["precautions_and_warnings"] = find_section_content(
            soup, "Precautions & Warnings"
        )
        medicine_item["overdose_effects"] = find_section_content(
            soup, "Overdose Effects"
        )

        return medicine_item

    except Exception as e:
        print(f"Error fetching {page_url}: {e}")
        return None


def scrape_brand_page(driver, page_number):
    url = f"{BRANDS_URL}{page_number}"

    # Add random delay before making request
    time.sleep(get_random_delay())

    try:
        driver.get(url)

        # Check for security check
        if (
            "security check" in driver.page_source.lower()
            or "captcha" in driver.page_source.lower()
        ):
            if not handle_security_check(driver):
                return [], False

        # Wait for page to load
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.hoverable-block"))
            )
        except TimeoutException:
            # Check again for security check
            if (
                "security check" in driver.page_source.lower()
                or "captcha" in driver.page_source.lower()
            ):
                if not handle_security_check(driver):
                    return [], False
                else:
                    # Try waiting again after security check
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "a.hoverable-block")
                        )
                    )

        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        medicine_links = soup.select("a.hoverable-block")
        links = [link.get("href") for link in medicine_links]

        next_page_link = soup.select_one('a.page-link[rel="next"]')
        has_next_page = next_page_link is not None

        return links, has_next_page

    except TimeoutException:
        print(f"Timeout while loading page {page_number}")
        return [], False
    except Exception as e:
        print(f"Error scraping page {page_number}: {e}")
        return [], False


def main_crawler(start_page=1, max_pages=None):
    driver = setup_driver()

    try:
        # First, visit the base URL to establish session
        driver.get(BASE_URL)
        print(f"Established session with {BASE_URL}")
        time.sleep(3)  # Allow time for page to load

        # Check for initial security check
        if (
            "security check" in driver.page_source.lower()
            or "captcha" in driver.page_source.lower()
        ):
            if not handle_security_check(driver):
                print("Initial security check failed. Exiting.")
                return

        page_number = start_page
        consecutive_errors = 0
        max_consecutive_errors = (
            3  # Reduced since we're handling security checks manually
        )

        while True:
            try:
                print(f"Scraping page {page_number}...")
                medicine_urls, has_next_page = scrape_brand_page(driver, page_number)

                if not medicine_urls:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(
                            f"Too many consecutive errors ({max_consecutive_errors}). Stopping."
                        )
                        break
                    print(
                        f"No medicine URLs found on page {page_number}. Trying next page."
                    )
                    page_number += 1
                    continue

                consecutive_errors = 0  # Reset error counter on successful page scrape

                # Randomize the order of processing URLs
                random.shuffle(medicine_urls)

                for url in medicine_urls:
                    details = extract_medicine_details(driver, url)
                    if details:
                        all_medicines.append(details)
                        print(
                            f"Scraped medicine: {details.get('brand_name', 'Unknown')}"
                        )
                    else:
                        print(f"Failed to scrape details from: {url}")

                if not has_next_page or (max_pages and page_number >= max_pages):
                    print(
                        "Finished crawling all available pages or reached the page limit."
                    )
                    break

                page_number += 1

                # Occasionally take a longer break
                if random.random() < 0.1:  # 10% chance
                    longer_break = random.uniform(15, 30)
                    print(f"Taking a longer break for {longer_break:.2f} seconds...")
                    time.sleep(longer_break)

            except Exception as e:
                consecutive_errors += 1
                print(f"Error on page {page_number}: {e}")
                if consecutive_errors >= max_consecutive_errors:
                    print(
                        f"Too many consecutive errors ({max_consecutive_errors}). Stopping."
                    )
                    break
                page_number += 1
                continue

    finally:
        driver.quit()

    # Create the data/processed directory if it doesn't exist
    output_dir = "data/drug_db"
    os.makedirs(output_dir, exist_ok=True)

    # Save the scraped data to a JSON file
    output_path = os.path.join(output_dir, "medex_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_medicines, f, ensure_ascii=False, indent=4)

    print(
        f"Successfully scraped {len(all_medicines)} medicine brands and saved to {output_path}"
    )


if __name__ == "__main__":
    main_crawler(max_pages=844)
