# backend/app/qdrant_helper.py
from qdrant_client import QdrantClient, models
import os
from typing import List, Optional, Dict, Any
from .utils import QDRANT_URL # Importamos la URL desde utils

# ==========================
# Configuración base
# ==========================
# QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333") # Ya no se define aquí
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

# Cliente global
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)

# ==========================
# Gestión de colecciones
# ==========================
def collection_exists(name: str) -> bool:
    """Verifica si una colección existe en Qdrant."""
    try:
        collections = client.get_collections().collections
        return any(c.name == name for c in collections)
    except Exception as e:
        print(f"Error al verificar colección: {e}")
        return False


def create_collection_if_missing(
    name: str,
    vector_size: int = 384,
    distance=models.Distance.COSINE,
    payload_indexes: Optional[List[str]] = None
):
    """
    Crea una colección optimizada con soporte para HNSW, quantization y payload index.
    """
    if collection_exists(name):
        return

    print(f"🧠 Creando colección optimizada '{name}'...")
    try:
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=distance,
                on_disk=False
            ),
            hnsw_config=models.HnswConfigDiff(
                m=32,
                ef_construct=256,
                full_scan_threshold=10000
            ),
            optimizers_config=models.OptimizersConfigDiff(
                memmap_threshold=20000,
                indexing_threshold=10000
            ),
            quantization_config=models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    quantile=0.99,
                    always_ram=True
                )
            )
        )

        # Indexar payloads comunes y personalizados
        default_indexes = ["document", "session_id", "page_number"]
        if payload_indexes:
            default_indexes.extend(payload_indexes)

        for field in set(default_indexes):
            try:
                client.create_payload_index(
                    collection_name=name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
            except Exception:
                pass

    except Exception as e:
        print(f"⚠️ Error creando colección '{name}': {e}")


def delete_collection(name: str):
    """Elimina una colección."""
    try:
        client.delete_collection(collection_name=name)
        print(f"🗑️ Colección '{name}' eliminada.")
    except Exception as e:
        print(f"⚠️ Error al eliminar colección '{name}': {e}")

# ==========================
# Funciones de inserción y actualización
# ==========================
def upsert_points(collection_name: str, points: List[models.PointStruct]):
    """Inserta o actualiza puntos en bloque."""
    try:
        client.upsert(collection_name=collection_name, points=points, wait=True)
    except Exception as e:
        print(f"⚠️ Error al upsert en '{collection_name}': {e}")


def update_vector(
    collection_name: str,
    point_id: str,
    new_vector: List[float],
    new_payload: Optional[Dict[str, Any]] = None
):
    """Actualiza vector y/o payload de un punto existente."""
    try:
        client.update(
            collection_name=collection_name,
            point_id=point_id,
            vector=new_vector,
            payload=new_payload
        )
    except Exception as e:
        print(f"⚠️ Error al actualizar vector en '{collection_name}', point_id={point_id}: {e}")


# ==========================
# Utilidades avanzadas
# ==========================
def list_collections() -> List[str]:
    """Devuelve todas las colecciones disponibles."""
    try:
        return [c.name for c in client.get_collections().collections]
    except Exception:
        return []


def search_similar(
    collection_name: str,
    query_vector: List[float],
    limit: int = 5,
    filters: Optional[Dict[str, Any]] = None
):
    """
    Busca puntos similares dentro de una colección, aplicando filtros.
    """
    filter_obj = None
    if filters:
        must_conditions = [
            models.FieldCondition(
                key=k,
                match=models.MatchValue(value=v)
            )
            for k, v in filters.items()
        ]
        filter_obj = models.Filter(must=must_conditions)

    try:
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_obj,
            with_payload=True # Aseguramos que siempre devuelva los metadatos
        )
        return results
    except Exception as e:
        print(f"⚠️ Error al buscar en '{collection_name}': {e}")
        return []

# ==========================
# Export
# ==========================
qdrant_client = client