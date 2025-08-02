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

