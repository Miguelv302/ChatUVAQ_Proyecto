# rag_engine.py
import re, uuid, logging
import numpy as np
import requests
from typing import List, Dict, Any, Optional
from qdrant_client import models

from app.qdrant_helper import create_collection_if_missing, upsert_points, list_collections
from app.utils import LLAMA_MODEL, LLMSTUDIO_URL, DEFAULT_TOP_K, RERANK_TOP_N, LLAMA_VECTOR_SIZE

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RAGEngine:
    def __init__(self, qdrant_client, embedder, chunk_size=500, multi_collection=False):
        self.qdrant = qdrant_client
        self.embedder = embedder
        self.chunk_size = chunk_size
        self.multi_collection = multi_collection

        # Detectar tamaño de vector real del embedder
        try:
            vec = self.embedder.encode("test")
            self.vector_size = len(vec)
        except Exception:
            self.vector_size = LLAMA_VECTOR_SIZE
            logger.warning(f"⚠️ Tamaño por defecto usado: {self.vector_size}")

        logger.info(f"Embedder activo. Vector size = {self.vector_size}")

    # ---------------------------
    # Colección única global
    # ---------------------------
    def ensure_collection(self, collection_name: str):
        create_collection_if_missing(collection_name, vector_size=self.vector_size)

    # -------------------------------------------------------
    # Indexación de documentos
    # -------------------------------------------------------
    def index_document_chunks(self, collection_name: str, chunks: List[Dict[str, Any]], document_id: Optional[str] = None):
        self.ensure_collection(collection_name)

        document_id = document_id or "unknown"
        points = []

        for chunk in chunks:
            text = chunk.get("text_content", "")
            if not text.strip():
                continue

            page_num = chunk.get("page_number")
            doc_id = chunk.get("source_document", document_id)

            # Extraer tema/subtema
            tema, subtema = self._extract_structure(text)

            # Dividir por párrafos
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 60]
            if not paragraphs:
                paragraphs = [text.strip()]

            for nivel, fragment in enumerate(paragraphs, start=1):
                emb = self.embedder.encode(fragment)
                vec = list(map(float, emb))

                payload = {
                    "text": fragment,
                    "document": doc_id,
                    "tema": tema,
                    "subtema": subtema,
                    "nivel": nivel,
                    "page_number": page_num,
                }

                points.append(
                    models.PointStruct(id=str(uuid.uuid4()), vector=vec, payload=payload)
                )

        if points:
            upsert_points(collection_name, points)
            logger.info(f"📌 Indexado completado: {len(points)} embeddings guardados.")

    # -------------------------------------------------------
    def _extract_structure(self, text: str):
        lines = text.split("\n")
        for l in lines[:5]:
            m = re.search(r"(?i)^(tema|capitulo|capítulo)\s+([0-9]+(\.[0-9]+)*)", l)
            if m:
                return m.group(2), "general"
        return "general", "sin_subtema"

    # -------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------
    def retrieve_candidates(self, collection_name: str, query: str, top_k=DEFAULT_TOP_K, filters=None):
        collections = list_collections()

        if collection_name not in collections:
            logger.warning("⚠️ No hay documentos cargados.")
            return []

        # Obtener vector consulta
        try:
            q_vector = list(map(float, self.embedder.encode(query)))
        except:
            q_vector = [0.0] * self.vector_size

        q_filter = None
        if filters:
            q_filter = models.Filter(
                must=[models.FieldCondition(key=k, match=models.MatchValue(value=v)) for k, v in filters.items()]
            )

        results = []

        try:
            hits = self.qdrant.search(
                collection_name=collection_name,
                query_vector=q_vector,
                limit=top_k,
                with_payload=True,
                query_filter=q_filter
            )

            for r in hits:
                pl = r.payload or {}
                results.append({
                    "id": r.id,
                    "text": pl.get("text", ""),
                    "score": r.score,
                    "document": pl.get("document"),
                    "page_number": pl.get("page_number"),
                    "tema": pl.get("tema"),
                    "subtema": pl.get("subtema"),
                })

        except Exception as e:
            logger.error(f"Error en búsqueda Qdrant: {e}")

        return results

    # -------------------------------------------------------
    # Reranking
    # -------------------------------------------------------
    def rerank_candidates(self, query: str, candidates: List[Dict], top_n=RERANK_TOP_N):
        if not candidates:
            return []

        try:
            qv = np.array(self.embedder.encode(query), dtype=float)
            qv = qv / (np.linalg.norm(qv) + 1e-10)
        except:
            return sorted(candidates, key=lambda x: x["score"], reverse=True)[:top_n]

        sims = []
        for c in candidates:
            try:
                tv = np.array(self.embedder.encode(c["text"]), dtype=float)
                tv = tv / (np.linalg.norm(tv) + 1e-10)
                sims.append((float(np.dot(qv, tv)), c))
            except:
                sims.append((c["score"], c))

        sims.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in sims][:top_n]

    # -------------------------------------------------------
    # Generación con LMStudio
    # -------------------------------------------------------
    def generate_answer(self, query: str, reranked: List[Dict], policy="strict", max_tokens=700):
        if not reranked:
            return "No pude encontrar información en los documentos cargados."

        ctx_parts = []
        for r in reranked:
            doc = r.get("document", "?")
            page = r.get("page_number", "?")
            text = r.get("text", "")

            ctx_parts.append(f"--- Fuente [doc: {doc}, pág: {page}] ---\n{text}")

        ctx = "\n\n".join(ctx_parts)

        prompt = f"""
Eres un asistente que responde usando ÚNICAMENTE la información del contexto.
Si no está en las fuentes, responde: "No hay información suficiente en los documentos."

Contexto:
{ctx}

Pregunta: {query}
"""

        try:
            payload = {
                "model": LLAMA_MODEL,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.0,
            }

            r = requests.post(f"{LLMSTUDIO_URL}/v1/completions", json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()

            return data.get("completion", "").strip()

        except Exception as e:
            logger.error(f"Error LMStudio: {e}")
            return reranked[0]["text"]
