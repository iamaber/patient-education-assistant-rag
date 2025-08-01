import json
import os
import time
import sys
from Bio import Entrez
from config.settings import NCBI_EMAIL, NCBI_API_KEY

Entrez.email = NCBI_EMAIL
Entrez.api_key = NCBI_API_KEY

def fetch_pubmed_id(query, max_results=100):
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"] 

def fetch_pubmed_abstracts(id_list, batch_size=20):
    abstracts = []
    for start in range(0, len(id_list), batch_size):
        batch_ids = id_list[start:start+batch_size]
        ids = ",".join(batch_ids)
        handle = Entrez.efetch(db="pubmed", id=ids, rettype="abstract", retmode="xml")
        records = Entrez.read(handle)
        handle.close()

        for article in records['PubmedArticle']:
            article_data = article['MedlineCitation']['Article']
            title = article_data.get('ArticleTitle', 'No Title')
            abstract_data = article_data.get('Abstract', {}).get('AbstractText', '')
            if isinstance(abstract_data, list):
                abstract_text = ' '.join([str(a) for a in abstract_data])
            elif isinstance(abstract_data, str):
                abstract_text = abstract_data
            else:
                abstract_text = ''

            pmid = article['MedlineCitation']['PMID']
            mesh_terms = [mesh['DescriptorName'] for mesh in article['MedlineCitation'].get('MeshHeadingList', [])]

            abstracts.append({
                "pmid": str(pmid),
                "title": str(title),
                "abstract": str(abstract_text),
                "mesh_terms": mesh_terms,
                "source": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })

        time.sleep(0.3)  # NCBI rate limits

    return abstracts

def save_to_json(data, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def fetch_and_save_pubmed_abstracts(query, max_results=100):
    for tag, query in SEARCH_QUERIES.items():
        ids = fetch_pubmed_ids(query, max_results=200)
        print(f"Found {len(ids)} articles.")

        abstracts = fetch_pubmed_abstracts(ids)
        # Auto-tagging source type
        source_type = "Bangladesh-specific" if "Bangladesh" in query else "Global"
        for doc in abstracts:
            doc["source_type"] = source_type

        output_file = f"data/processed/{tag}.json"
        save_to_json(abstracts, output_file)