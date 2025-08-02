import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "https://medex.com.bd"
BRANDS_URL = f"{BASE_URL}/brands?page="

# List of scraped medicine data
all_medicines = []


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


def extract_medicine_details(page_url):
    try:
        response = requests.get(page_url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, "html.parser")
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

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {page_url}: {e}")
        return None
    except AttributeError:
        print(f"Could not find all data on page: {page_url}. Skipping.")
        return None


def scrape_brand_page(page_number):
    url = f"{BRANDS_URL}{page_number}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    medicine_links = soup.select("a.hoverable-block")
    links = [link.get("href") for link in medicine_links]

    next_page_link = soup.select_one('a.page-link[rel="next"]')
    has_next_page = next_page_link is not None

    return links, has_next_page


def main_crawler(start_page=1, max_pages=None):
    page_number = start_page
    while True:
        medicine_urls, has_next_page = scrape_brand_page(page_number)
        if not medicine_urls:
            break

        for url in medicine_urls:
            details = extract_medicine_details(url)
            if details:
                all_medicines.append(details)
            time.sleep(1)

        if not has_next_page or (max_pages and page_number >= max_pages):
            print("Finished crawling all available pages or reached the page limit.")
            break

        page_number += 1
        time.sleep(1)

    # Create the data/processed directory if it doesn't exist
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)

    # Save the scraped data to a JSON file in data/processed directory
    output_path = os.path.join(output_dir, "medex_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_medicines, f, ensure_ascii=False, indent=4)

    print(
        f"Successfully scraped {len(all_medicines)} medicine brands and saved to {output_path}"
    )


if __name__ == "__main__":
    main_crawler(max_pages=822)
