import json
import logging
import re
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
import os

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("medex")


class MedexScraper:
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
        # Fetch markdown content from Jina reader
        try:
            response = self.session.get(self.JINA_BASE + url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            log.error("Failed to fetch %s: %s", url, exc)
            return None

    def discover_total_pages(self, markdown: str) -> int:
        # Extract highest page number from pagination links in markdown
        pattern = re.compile(r"\[(\d+)\]\([^)]*\bpage=(\d+)\)")
        pages = [int(page) for _, page in pattern.findall(markdown)]
        if pages:
            return max(pages)
        log.warning("Could not detect pagination; defaulting to 1 page")
        return 1

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
        # Convert relative URLs to absolute.
        if href.startswith("/"):
            return urljoin("https://medex.com.bd", href)
        if not href.startswith("http"):
            return urljoin("https://medex.com.bd/", href)
        return href

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
        log.info("Discovered %d total pages", total_pages)

        for page in range(2, total_pages + 1):
            url = f"{self.BASE_URL}?page={page}"
            md = self.fetch_markdown(url)
            if md:
                brands.extend(self.extract_brands(md))
            if page % 50 == 0 or page == total_pages:
                log.info(
                    "Progress: page %d/%d | brands so far: %d",
                    page,
                    total_pages,
                    len(brands),
                )
            time.sleep(delay)

        return brands

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
        log.info("Saved %d brands", len(data))


def main():
    scraper = MedexScraper()
    brands = scraper.scrape_all_pages(max_pages=1, delay=0.5)
    # brands = scraper.scrape_all_pages(delay=1.0)  # Uncomment for full run

    if brands:
        scraper.save_json(brands)
        print(f"Total brands: {len(brands)}")

    else:
        print("Nothing scraped – check logs above")


if __name__ == "__main__":
    main()
