# rag_engine_llama.py
import re, uuid, logging
import numpy as np
from typing import List, Dict, Any, Optional
from qdrant_client import models
from .qdrant_helper import create_collection_if_missing, upsert_points, list_collections
from .utils import DEFAULT_TOP_K, RERANK_TOP_N, LLAMA_MODEL, LLMSTUDIO_URL, LLAMA_VECTOR_SIZE
from .embedder_llama import LlamaEmbedder
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RAGEngine:
    def __init__(self, qdrant_client, embedder=None, chunk_size=500, multi_collection=False):    
        self.qdrant = qdrant_client    
        self.qdrant = qdrant_client
        self.embedder = embedder or LlamaEmbedder()
        self.chunk_size = chunk_size
        self.multi_collection = multi_collection

        try:
            vec = self.embedder.encode("test")
            self.vector_size = len(vec) if hasattr(vec, "__len__") else LLAMA_VECTOR_SIZE
            logger.info(f"✅ Embedder cargado. Vector size = {self.vector_size}")
        except Exception:
            self.vector_size = LLAMA_VECTOR_SIZE
            logger.warning(f"⚠️ Tamaño por defecto {self.vector_size}")
    
    def _collection_name(self, session_id: str, tema: Optional[str] = None) -> str:
        return f"knowledge_{session_id}"

    def ensure_collection(self, session_id: str):
        name = self._collection_name(session_id)
        create_collection_if_missing(name, vector_size=self.vector_size)
        return name

    def _extract_structure(self, text: str):
        lines = text.split("\n")
        for l in lines[:5]:
            m = re.search(r"(?im)^(?:tema|cap[ií]tulo|capitulo)\s+([0-9]+(?:\.[0-9]+)*)", l)
            if m:
                return m.group(1), "general"
        return "general", "sin_subtema"

    def index_document_chunks(self, session_id: str, chunks: List[Dict[str, Any]], document_id: Optional[str] = None):
        document_id = document_id or "unknown"
        points = []
        collection = self.ensure_collection(session_id)
        
        for chunk in chunks:
            text = chunk.get("text_content", "")
            if not text.strip():
                continue
            page_num = chunk.get("page_number")
            doc_id = chunk.get("source_document", document_id)
            tema, subtema = self._extract_structure(text)

            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 60]
            if not paragraphs:
                paragraphs = [text.strip()]

            for nivel, fragment in enumerate(paragraphs, start=1):
                emb = self.embedder.encode(fragment)
                vec = list(map(float, emb))
                payload = {
                    "text": fragment,
                    "document": doc_id,
                    "session_id": session_id,
                    "tema": tema,
                    "subtema": subtema,
                    "nivel": nivel,
                    "page_number": page_num
                }
                points.append(models.PointStruct(id=str(uuid.uuid4()), vector=vec, payload=payload))

            if points:
                upsert_points(collection, points)
                points.clear()       
        
        logger.info(f"✅ Indexado completado: {len(chunks)} chunks para {document_id}")

    def retrieve_candidates(self, session_id: str, query: str, top_k=DEFAULT_TOP_K, filters=None) -> List[dict]:
        collections = [c for c in list_collections() if c.startswith(f"knowledge_{session_id}")]
        if not collections:
            logger.info("No hay colecciones para la sesión.")
            return []

        try:
            q_vector = list(map(float, self.embedder.encode(query)))
        except Exception:
            q_vector = [0.0] * self.vector_size

        combined = {}
        q_filter = None
        if filters:
            q_filter = models.Filter(
                must=[models.FieldCondition(key=k, match=models.MatchValue(value=v)) for k, v in filters.items()]
            )

        for col in collections:
            try:
                hits = self.qdrant.search(
                    collection_name=col,
                    query_vector=q_vector,
                    limit=top_k,
                    with_payload=True,
                    query_filter=q_filter
                )
                for r in hits:
                    if r.id not in combined:
                        pl = getattr(r, "payload", {}) or {}
                        combined[r.id] = {
                            "id": r.id,
                            "text": pl.get("text", ""),
                            "score": getattr(r, "score", 0.0),
                            "document": pl.get("document"),
                            "page_number": pl.get("page_number"),
                            "tema": pl.get("tema"),
                            "subtema": pl.get("subtema"),
                        }
            except Exception as e:
                logger.warning(f"Error búsqueda en {col}: {e}")

        return sorted(combined.values(), key=lambda x: x["score"], reverse=True)[:top_k]

    def _embed_score_rerank(self, query: str, candidates: List[Dict], top_n: int):
        try:
            qv = np.array(self.embedder.encode(query), dtype=float)
            qv = qv / (np.linalg.norm(qv) + 1e-10)
        except Exception:
            return sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)[:top_n]
        sims = []

        for c in candidates:
            try:
                tv = np.array(self.embedder.encode(c["text"]), dtype=float)
                tv = tv / (np.linalg.norm(tv) + 1e-10)
                sims.append((float(np.dot(qv, tv)), c))
            except Exception:
                sims.append((c.get("score", 0), c))
        sims.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in sims][:top_n]

    def rerank_candidates(self, query: str, candidates: List[Dict], top_n=RERANK_TOP_N) -> List[Dict]:
        if not candidates:
            return []
        return self._embed_score_rerank(query, candidates, top_n)

    def generate_answer(self, query: str, reranked_results: List[Dict], policy: str = "strict", max_tokens: int = 700) -> str:
        if not reranked_results:
            return "No pude encontrar información sobre ese tema en los documentos cargados."

        context_parts = []
        for r in reranked_results:
            doc = r.get("document", "?")
            page_label = "pág" if isinstance(doc, str) and doc.lower().endswith(".pdf") else "grupo"
            page_num = r.get("page_number", "?")
            text = r.get("text", "")
            context_parts.append(f"--- Fuente [doc: {doc}, {page_label}: {page_num}] ---\n{text}")

        ctx = "\n\n".join(context_parts)

        if policy == "inferential":
            prompt = f"""
Eres un asistente que puede inferir a partir del contexto provisto. Si algo es inferencia, indícalo.
Contexto:
{ctx}
Pregunta: {query}
"""
        else:
            prompt = f"""
Eres un asistente de IA factual y preciso. Responde la pregunta usando únicamente las fuentes de contexto y cita con [doc: nombre, pág: X] o [doc: nombre, grupo: X].
Contexto:
{ctx}
Pregunta: {query}
"""

        try:
            payload = {
                "model": LLAMA_MODEL,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.0
            }
            resp = requests.post(f"{LLMSTUDIO_URL}/v1/completions", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("completion", "").strip()
            if not answer:
                return "No pude generar una respuesta a partir de las fuentes."
            return answer
        except Exception as e:
            logger.warning(f"Error LLM al generar respuesta: {e}")
            best = reranked_results[0]
            snippet = best.get("text", "")
            return f"No pude generar la respuesta por un error interno. Fragmento más relevante:\n{snippet}"