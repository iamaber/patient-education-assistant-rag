import requests
import json
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv
from config.settings import GEMINI_MODEL_NAME

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(GEMINI_MODEL_NAME)

JINA_BASE = "https://r.jina.ai/"

# Dosage units for strength extraction
DOSAGE_UNITS = ("mg", "ml", "iu", "mcg", "%")


def extract_strength_regex(content):
    if not content:
        return None

    units_pattern = "|".join(DOSAGE_UNITS)

    patterns = [
        # Pattern 1: Standard format like "100 mg", "5 ml", "200 mg + 100 mcg"
        rf"(\d+(?:\.\d+)?\s*(?:{units_pattern})(?:\s*[+\-]\s*\d+(?:\.\d+)?\s*(?:{units_pattern}))*)",
        # Pattern 2: Strength in parentheses or after colon
        rf"strength[:\s]*(\d+(?:\.\d+)?\s*(?:{units_pattern})(?:\s*[+\-]\s*\d+(?:\.\d+)?\s*(?:{units_pattern}))*)",
        # Pattern 3: After "Each" or "Contains"
        rf"(?:each|contains)[:\s]*(\d+(?:\.\d+)?\s*(?:{units_pattern})(?:\s*[+\-]\s*\d+(?:\.\d+)?\s*(?:{units_pattern}))*)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def extract_with_gemini(markdown_content, brand_name):
    prompt = f"""
You are an expert in parsing and extracting **structured medical drug information** from markdown-formatted drug pages (source: MedEx Bangladesh).  
Your task: produce a clean, **English-only JSON object** with the required fields, translating any non-English text (e.g., Bengali) to English.  

Carefully read the entire document before extraction. Do not stop at the first match — search the full text for each item.  
Maintain original medical details without paraphrasing unless translating from Bengali.

Required JSON structure:
{{
  "brand_name": "{brand_name}",
  "generic_name": "Exact English generic name found in parentheses in the title/subtitle or look for the first part for generic_name.",
  "manufacturer_name": "Full company name (e.g., 'Square Pharmaceuticals Ltd.').",
  "dosage_form": "Single form like Tablet, Capsule, Syrup, Injection, etc.",
  "strength": "Exact dosage (e.g., '100 mg', '200 mg+200 mcg') and DOSAGE_UNITS = ('mg', 'ml', 'iu', 'mcg', '%').",
  "unit_price": "Numeric value only from 'Unit Price: ৳'.",
  "strip_price": "Numeric value only from 'Strip Price: ৳'.",
  "Indications": "Full text under the 'Indications' heading.",
  "Composition": "Full text under the 'Composition' heading.",
  "Pharmacology": "Full text under the 'Pharmacology' heading.",
  "Dosage & Administration": "Full text under the 'Dosage & Administration' heading.",
  "Interaction": "Full text under the 'Interaction' heading.",
  "Contraindications": "Full text under the 'Contraindications' heading.",
  "Side Effects": "Full text under the 'Side Effects' heading.",
  "Pregnancy & Lactation": "Full text under the 'Pregnancy & Lactation' heading.",
  "Precautions & Warnings": "Full text under the 'Precautions & Warnings' heading.",
  "Overdose Effects": "Full text under the 'Overdose Effects' heading.",
  "Therapeutic Class": "Full text under the 'Therapeutic Class' heading.",
  "Storage Conditions": "Full text under the 'Storage Conditions' heading."
}}

Extraction Rules:
1. **Scan the entire document** for each field, including content at the very end.
2. If a field explicitly states "No information available" or equivalent, include that phrase.
3. Only set a value to `null` if it’s **truly absent**.
4. **generic_name** → prioritize English version inside parentheses; if absent, translate Bengali version.
5. **manufacturer_name** → match common patterns (e.g., ends with 'Ltd.', 'Limited', 'Pharma', 'Pharmaceuticals').
6. **Prices** → remove currency symbols, return only numeric values (e.g., `12.5`).
7. **Section content** → capture the entire section text until the next heading or document end.
8. Translate any Bengali text into accurate English while preserving drug details.

Additional Instructions:
- If generic_name, manufacturer_name, strength, or dosage_form are already provided in the JSON, 
  only override them if you find definitive conflicting information in the scraped content
- For null values in JSON, attempt to extract from the page

Output format:
- **Return only the JSON object** — no extra text, comments, or explanations.

Markdown source content:
{markdown_content}
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        data = json.loads(response_text)

        # Enhance strength extraction - try both Gemini result and regex
        if not data.get("strength") or data.get("strength") == "null":
            regex_strength = extract_strength_regex(markdown_content)
            if regex_strength:
                data["strength"] = regex_strength
        return data

    except Exception as e:
        return {"brand_name": brand_name, "error": f"Gemini API error: {str(e)}"}


def merge_brand_info(json_brand, scraped_data):
    """
    Merge brand information from JSON with scraped data.
    Prioritizes existing non-null values from JSON, but fills in null values with scraped data.
    """
    # Start with the scraped data as base
    merged = scraped_data.copy()

    # Fields to merge from JSON data
    merge_fields = ["generic_name", "manufacturer_name", "strength", "dosage_form"]

    # For each field, if JSON has a non-null value, use it; otherwise keep scraped value
    for field in merge_fields:
        json_value = json_brand.get(field)
        scraped_value = scraped_data.get(field)

        # If JSON has a non-null value, use it
        if json_value is not None:
            merged[field] = json_value
        # If JSON value is null but scraped data has a value, keep scraped value
        elif scraped_value is not None:
            merged[field] = scraped_value
        # If both are null, keep null

    # Ensure brand name is consistent
    merged["brand_name"] = json_brand.get("brand_name", scraped_data.get("brand_name"))

    return merged


def process_brands_with_gemini(input_file, output_file, start_index=0):
    with open(input_file, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    brands = input_data.get("brands", [])
    results = []
    total_brands = len(brands)

    if start_index > 0 and os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            results = json.load(f)

    for i in range(start_index, total_brands):
        brand = brands[i]
        brand_name = brand.get("brand_name", "Unknown")

        try:
            jina_url = JINA_BASE + brand["brand_url"]
            response = requests.get(jina_url, timeout=30)
            response.raise_for_status()

            medicine_info = extract_with_gemini(response.text, brand_name)
            # Merge the JSON brand info with scraped data
            merged_info = merge_brand_info(brand, medicine_info)
            results.append(merged_info)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"Medicine {i + 1} scraped: {brand_name}")

        except Exception as e:
            # Even if scraping fails, keep the original JSON data
            error_info = brand.copy()
            error_info["error"] = str(e)
            results.append(error_info)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"Medicine {i + 1} failed: {brand_name}")

    print(f"\nCompleted! Processed {len(results)} medicines.")


if __name__ == "__main__":
    input_json = "data/drug_db/medex_URL.json"
    output_json = "data/drug_db/medex_details.json"

    start_index = 0
    if os.path.exists(output_json):
        with open(output_json, "r", encoding="utf-8") as f:
            try:
                results = json.load(f)
                start_index = len(results)
                print(f"Resuming from medicine {start_index + 1}")
            except Exception:
                pass

    if not os.path.exists(input_json):
        print(f"Input file not found: {input_json}")
        exit(1)

    process_brands_with_gemini(input_json, output_json, start_index)
