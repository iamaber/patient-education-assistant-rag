import json
import os
import time
import sys
from Bio import Entrez
from config.settings import NCBI_EMAIL, NCBI_API_KEY

Entrez.email = NCBI_EMAIL
Entrez.api_key = NCBI_API_KEY

def fetch_pubmed_id(query, maxresults=100):
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]
