# qdrant_helper.py
from qdrant_client import QdrantClient, models
import logging

logger = logging.getLogger(__name__)

QDRANT_COLLECTION = "docs"
EMBED_DIM = 768  # nomic-text-v1.5

client = QdrantClient(url="http://localhost:6333")

def create_collection_if_missing():
    collections = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        logger.info("Creando colección Qdrant...")
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(
                size=EMBED_DIM,
                distance=models.Distance.COSINE
            )
        )
        logger.info("Colección creada.")

def upsert_points(points):
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points
    )
