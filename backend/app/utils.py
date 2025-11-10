# backend/app/utils.py
import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Apunta al nombre del servicio en docker-compose
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant-db:6333") 

RAG_MODE = os.getenv("RAG_MODE", "hybrid+hyde").lower()
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))