import os
from dotenv import load_dotenv

load_dotenv()

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

# RAG settings
RAG_MODE = os.getenv("RAG_MODE", "hybrid+hyde").lower()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", 10))
RERANK_TOP_N = int(os.getenv("RERANK_TOP_N", 5))

# LLaMA / LMStudio
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "text-embedding-nomic-embed-text-v1.5")
LLMSTUDIO_URL = os.getenv("LLMSTUDIO_URL", "http://127.0.0.1:1234")
LLAMA_VECTOR_SIZE = int(os.getenv("LLAMA_VECTOR_SIZE", 768))  # tamaño del embedding LLaMA

# Admin token (simple protection)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me")
