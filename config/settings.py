import os
from dotenv import load_dotenv

load_dotenv()

NCBI_EMAIL = os.getenv("NCBI_EMAIL")
NCBI_API_KEY = os.getenv("NCBI_API_KEY")

