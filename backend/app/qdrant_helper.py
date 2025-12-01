# qdrant_helper.py
import logging
from qdrant_client import QdrantClient, models

logger = logging.getLogger(__name__)

# Colección única global
QDRANT_URL = "http://localhost:6333"

qdrant_client = QdrantClient(url=QDRANT_URL)


def create_collection_if_missing(collection_name: str, vector_size: int):
    """
    Crea una colección si no existe. Usa tamaño del embedding dinámico.
    """
    existing = [c.name for c in qdrant_client.get_collections().collections]

    if collection_name not in existing:
        logger.info(f"Creando colección Qdrant '{collection_name}' con vector size {vector_size}...")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE
            )
        )
        logger.info("Colección creada correctamente.")
    else:
        logger.info(f"La colección '{collection_name}' ya existe.")


def upsert_points(collection_name: str, points):
    """
    Inserta embeddings/chunks en Qdrant.
    """
    qdrant_client.upsert(collection_name=collection_name, points=points)


def list_collections():
    """
    Retorna lista de nombres de colecciones.
    """
    return [c.name for c in qdrant_client.get_collections().collections]
