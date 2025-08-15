import json
import logging
import os
import re
import time
from textwrap import dedent
from typing import Dict, List, Optional
from urllib.parse import urljoin
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from config.settings import GEMINI_MODEL_NAME

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("medex")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

BRAND_INFO_PROMPT = dedent("""
You are a drug database assistant.
Read the markdown text below and return ONLY a single, valid JSON object with the following keys:

- generic_name      (string, comma-separated if multiple, or null if not found)
- manufacturer_name (string, or null if not found)
- strength          (string, e.g. "200 mg", or null if not found)
- dosage_form       (string, e.g. "tablet", or null if not found)

IMPORTANT:
- Return ONLY valid JSON, no markdown fences, no extra text
- If any information is missing, use null for that field
- Do not add comments or explanations
- Ensure the JSON is properly formatted

Example response:
{{"generic_name": "Paracetamol", "manufacturer_name": "Square Pharmaceuticals", "strength": "500 mg", "dosage_form": "tablet"}}

Markdown:
{markdown}
""")


class MedexGeminiScraper:
    BASE_URL = "https://medex.com.bd/brands"
    JINA_BASE = "https://r.jina.ai/"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    )
    DOSAGE_UNITS = ("mg", "ml", "iu", "mcg", "%")

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    def fetch_markdown(self, url: str) -> Optional[str]:
        try:
            response = self.session.get(self.JINA_BASE + url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            log.error("Failed to fetch %s: %s", url, exc)
            return None

    def discover_total_pages(self, markdown: str) -> int:
        pattern = re.compile(r"\[(\d+)\]\([^)]*\bpage=(\d+)\)")
        pages = [int(page) for _, page in pattern.findall(markdown)]
        return max(pages) if pages else 1

    def extract_brands(self, markdown: str) -> List[Dict[str, str]]:
        link_pattern = re.compile(r"!\[.*?\]\([^)]+\)\s*(.*?)\]\(([^)]+)\)")
        brands = []
        for text, href in link_pattern.findall(markdown):
            brand_name = self._parse_brand_name(text)
            if not brand_name:
                continue
            brand_url = self._make_absolute_url(href.strip())
            brands.append({"brand_name": brand_name, "brand_url": brand_url})
        return brands

    def _parse_brand_name(self, text: str) -> str:
        tokens = text.strip().split()
        idx = next(
            (
                i
                for i, tok in enumerate(tokens)
                if any(u in tok.lower() for u in self.DOSAGE_UNITS)
            ),
            None,
        )
        brand_name = " ".join(tokens[:idx]) if idx is not None else " ".join(tokens[:3])
        brand_name = re.sub(r"[^\w\s\-]", "", brand_name).strip()
        return brand_name

    def _make_absolute_url(self, href: str) -> str:
        if href.startswith("/"):
            return urljoin("https://medex.com.bd", href)
        if not href.startswith("http"):
            return urljoin("https://medex.com.bd/", href)
        return href

    def enrich_brand(
        self, brand: Dict[str, str], max_retries: int = 2
    ) -> Dict[str, str]:
        detail_md = self.fetch_markdown(brand["brand_url"])
        if not detail_md:
            return brand

        for attempt in range(max_retries + 1):
            try:
                model = genai.GenerativeModel(GEMINI_MODEL_NAME)
                response = model.generate_content(
                    BRAND_INFO_PROMPT.format(markdown=detail_md)
                )

                if not response or not response.text:
                    if attempt < max_retries:
                        time.sleep(2)
                        continue
                    return brand

                response_text = response.text.strip()
                if not response_text:
                    if attempt < max_retries:
                        time.sleep(2)
                        continue
                    return brand

                try:
                    parsed = json.loads(response_text)
                    if isinstance(parsed, dict):
                        brand.update(parsed)
                        return brand
                    else:
                        if attempt < max_retries:
                            time.sleep(2)
                            continue
                        return brand

                except json.JSONDecodeError:
                    if attempt < max_retries:
                        time.sleep(2)
                        continue
                    return brand

            except Exception:
                if attempt < max_retries:
                    time.sleep(2)
                    continue

        return brand

    def scrape_all_pages(
        self, max_pages: Optional[int] = None, delay: float = 1.0
    ) -> List[Dict[str, str]]:
        first_md = self.fetch_markdown(self.BASE_URL)
        if not first_md:
            log.error("Cannot fetch first page – aborting")
            return []

        brands = self.extract_brands(first_md)
        total_pages = self.discover_total_pages(first_md)
        if max_pages:
            total_pages = min(total_pages, max_pages)

        log.info(
            "Starting to scrape %d pages with %d initial brands",
            total_pages,
            len(brands),
        )

        for page in range(2, total_pages + 1):
            url = f"{self.BASE_URL}?page={page}"
            md = self.fetch_markdown(url)
            if md:
                brands.extend(self.extract_brands(md))
            time.sleep(delay)

        enriched = []
        for i, brand in enumerate(brands):
            enriched_brand = self.enrich_brand(brand)
            enriched.append(enriched_brand)

            if i > 0 and i % 10 == 0:
                print(f"Processed {i}/{len(brands)} brands")
                time.sleep(2)
            elif i > 0:
                time.sleep(0.5)

        return enriched

    @staticmethod
    def save_json(data: List[Dict[str, str]], filename: str = "medex_URL.json"):
        out_dir = "./data/drug_db"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, filename)
        payload = {
            "total_brands": len(data),
            "scrape_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "brands": data,
        }
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        log.info("Saved %d brands to %s", len(data), out_path)


def main():
    scraper = MedexGeminiScraper()
    brands = scraper.scrape_all_pages(max_pages=1, delay=0.5)
    if brands:
        scraper.save_json(brands)
        print(f"Total brands: {len(brands)}")
    else:
        print("No brands scraped")


if __name__ == "__main__":
    main()
