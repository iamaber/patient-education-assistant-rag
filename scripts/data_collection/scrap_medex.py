import requests
from bs4 import BeautifulSoup
import re
import json
import time

BASE_URL = 'https://medex.com.bd'
BRANDS_URL = f'{BASE_URL}/brands?page='

# List of scraped medicine data
all_medicines = []

def clean_text(text):
    if text:
        return ' '.join(text.strip().split())
    return None

def find_section_content(soup, heading_text):
    # find the heading element containing text
    heading = soup.find(['h3', 'h4', 'h5'], string=lambda t: t and heading_text in t)
    
    if heading:
        parent_div = heading.parent
        content_div = parent_div.find_next_sibling()

        if content_div and 'ac-body' in content_div.get('class', []):
            return clean_text(content_div.get_text(separator=' ', strip=True))
    return None


def extract_medicine_details(page_url):
    try:
        response = requests.get(page_url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        medicine_item = {}
        # brand name
        brand_name = soup.select_one('h1.page-heading-1-l')
        medicine_item['brand_name'] = clean_text(brand_name.text) if brand_name else None
      
        generic_info = soup.select_one('div[title="Generic Name"] a')
        if generic_info:
            medicine_item['generic_name'] = clean_text(generic_info.text)
        else:
            medicine_item['generic_name'] = None
        # Manufacturer Name
        manufacturer_info = soup.find('div', title='Manufactured by')
        if manufacturer_info:
            manufacturer_name_tag = manufacturer_info.find('a')
            medicine_item['manufacturer_name'] = clean_text(manufacturer_name_tag.text) if manufacturer_name_tag else None
        else:
            medicine_item['manufacturer_name'] = None
        # Dosage Form
        dosage_form_tag = soup.select_one('h1.page-heading-1-l small[title="Dosage Form"]')
        if dosage_form_tag:
            medicine_item['dosage_form'] = clean_text(dosage_form_tag.text)
        else:
            medicine_item['dosage_form'] = None
        # Strength
        strength = soup.select_one('div[title="Strength"]')
        medicine_item['strength'] = clean_text(strength.text) if strength else None
        
        # Unit Price
        price_info = soup.find('div', class_='package-container')
        if price_info:
            price_span = price_info.find_all('span')
            if len(price_span) > 1:
                medicine_item['unit_price'] = clean_text(price_span[1].text)
            else:
                medicine_item['unit_price'] = None
        else:
            medicine_item['unit_price'] = None
        
        medicine_item['indications'] = find_section_content(soup, 'Indications')
        medicine_item['pharmacology'] = find_section_content(soup, 'Pharmacology')
        medicine_item['dosage_and_administration'] = find_section_content(soup, 'Dosage & Administration')
        medicine_item['contraindications'] = find_section_content(soup, 'Contraindications')
        medicine_item['side_effects'] = find_section_content(soup, 'Side Effects')
        medicine_item['pregnancy_and_lactation'] = find_section_content(soup, 'Pregnancy & Lactation')
        medicine_item['precautions_and_warnings'] = find_section_content(soup, 'Precautions & Warnings')
        medicine_item['overdose_effects'] = find_section_content(soup, 'Overdose Effects')
            
        return medicine_item
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {page_url}: {e}")
        return None
    except AttributeError:
        print(f"Could not find all data on page: {page_url}. Skipping.")
        return None
    
    