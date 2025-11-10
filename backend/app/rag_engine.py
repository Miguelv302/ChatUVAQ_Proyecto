# backend/app/rag_engine.py
import re
import math
import uuid
from collections import defaultdict, Counter
from typing import List, Optional, Union, Dict, Any, Tuple
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, PointStruct, Distance
)
from qdrant_client import QdrantClient
from openai import OpenAI

# helpers
from .qdrant_helper import (
    create_collection_if_missing,
    upsert_points,
    list_collections,
    search_similar
)

_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)


def simple_tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text)]


# === BM25 clásico (No se usa en este flujo, pero se mantiene por si RAG_MODE lo necesita) ===
class BM25Index:
    def __init__(self, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.tf: List[Counter] = []
        self.df: Dict[str, int] = defaultdict(int)
        self.N = 0
        self.avgdl = 0.0

    def add_document(self, text: str):
        tokens = simple_tokenize(text)
        self.docs.append(tokens)
        self.doc_lengths.append(len(tokens))
        counts = Counter(tokens)
        self.tf.append(counts)
        for t in counts:
            self.df[t] += 1
        self.N += 1
        self.avgdl = sum(self.doc_lengths) / self.N if self.N else 0.0
        return len(self.docs) - 1

    def score(self, query: str) -> List[float]:
        q_tokens = simple_tokenize(query)
        scores = [0.0] * self.N
        for idx in range(self.N):
            dl = self.doc_lengths[idx]
            for term in q_tokens:
                f = self.tf[idx].get(term, 0)
                if not f:
                    continue
                idf = math.log((self.N - self.df.get(term, 0) + 0.5) /
                             (self.df.get(term, 0) + 0.5) + 1.0)
                denom = f + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1.0))
                scores[idx] += idf * (f * (self.k1 + 1)) / denom
        return scores

    def clear(self):
        self.docs.clear()
        self.doc_lengths.clear()
        self.df.clear()
        self.tf.clear()
        self.N = 0
        self.avgdl = 0.0


# === 🧠 RAG Engine híbrido ===
class RAGEngine:
    def __init__(
        self,
        qdrant_client: QdrantClient,
        embedder,
        openai_client: OpenAI,
        chunk_size: int = 500,
        multi_collection: bool = True # Lo mantenemos por si se re-activa
    ):
        self.qdrant = qdrant_client
        self.embedder = embedder
        self.openai = openai_client
        self.chunk_size = chunk_size
        self.multi_collection = multi_collection
        self.sessions_bm25: Dict[str, BM25Index] = {}
        self.session_contexts: Dict[str, str] = {}
        self.nivel_pesos = {1: 0.8, 2: 1.0, 3: 0.9}
        self.hyde_model = "gpt-4o-mini"
        self.rerank_model = "gpt-4o-mini"

    def update_context(self, session_id: str, message: str, answer: str):
        self.session_contexts[session_id] = answer # Ejemplo de caché simple
        pass

    # =======================
    # 🔹 Colección dinámica
    # =======================
    def _collection_name(self, session_id_or_global: str, tema: Optional[str] = None) -> str:
        """
        Genera un nombre de colección. 
        Si 'session_id_or_global' no es un UUID, lo trata como un nombre global.
        """
        try:
            # Intenta parsear como UUID. Si falla, es un nombre global.
            uuid.UUID(session_id_or_global)
            prefix = f"knowledge_{session_id_or_global}"
        except ValueError:
            prefix = session_id_or_global # Ej: "uvaq_main_knowledge"

        if self.multi_collection and tema:
            safe_tema = re.sub(r"[^a-zA-Z0-9_-]", "_", tema.lower())[:40]
            return f"{prefix}_{safe_tema}"
        return prefix

    def ensure_collection(self, session_id_or_global: str, tema: Optional[str] = None):
        name = self._collection_name(session_id_or_global, tema)
        create_collection_if_missing(
            name, vector_size=384, distance=Distance.COSINE,
            payload_indexes=["tema", "subtema", "nivel", "document", "page_number"]
        )
        if session_id_or_global not in self.sessions_bm25:
            self.sessions_bm25[session_id_or_global] = BM25Index()
        return name

    # =======================
    # 🔹 Extracción jerárquica
    # =======================
    def _extract_structure(self, text: str) -> Tuple[str, str]:
        """
        Extrae la clave del tema/subtema (ej. "2.1") para que coincida con el parser.
        """
        first_line = text.split('\n')[0].strip()
        
        match = re.search(r"(?im)^(?:tema|cap[ií]tulo|capitulo)\s+([a-zA-Z0-9\._\-]+)", first_line)
        if match:
            key = match.group(1) # "2.1"
            return key, "general" 

        match_sub = re.search(r"(?im)^(?:subtema|secci[oó]n)\s+([a-zA-Z0-9\._\-]+)", first_line)
        if match_sub:
            key_sub = match_sub.group(1) # "2.1.1"
            return "general", key_sub

        match_num = re.search(r"(?im)^\s*([0-9]+(?:\.[0-9]+)+)\s+[:\-]?\s*(.+)$", first_line)
        if match_num and len(first_line) < 200:
            key = match_num.group(1) 
            parts = key.split('.')
            if len(parts) == 2: return key, "general"
            if len(parts) > 2: return "general", key
        
        return "general", "sin_subtema"


    # =======================
    # 🔹 Indexar documento
    # =======================
    def index_document_chunks(
        self, 
        collection_id: str, # ID de colección global o de sesión
        chunks: List[Dict[str, Any]], 
        document_id: Optional[str] = None
    ):
        document_id = (document_id or "unknown").strip().lower()
        tema_actual, subtema_actual = "general", "sin_subtema"
        points: List[PointStruct] = []

        total_pages = len(chunks)
        for i, page_chunk in enumerate(chunks):
            
            if (i + 1) % 10 == 0 or i == 0 or i == total_pages - 1:
                print(f"      ➡️ Procesando Chunk/Página {i+1}/{total_pages}...")

            chunk = page_chunk.get("text_content", "")
            page_num = page_chunk.get("page_number")
            doc_id = page_chunk.get("source_document", document_id) 

            nuevo_tema, nuevo_subtema = self._extract_structure(chunk)
            if nuevo_tema != "general":
                tema_actual = nuevo_tema
            if nuevo_subtema != "sin_subtema":
                subtema_actual = nuevo_subtema

            collection = self.ensure_collection(collection_id, tema_actual if self.multi_collection else None)

            if collection_id not in self.sessions_bm25:
                self.sessions_bm25[collection_id] = BM25Index()
            self.sessions_bm25[collection_id].add_document(chunk)

            # Estrategia de Nivel 2: Solo párrafos (más rápido)
            paragraphs = [p.strip() for p in re.split(r'\n{1,}', chunk) if len(p.strip()) > 80]
            
            levels = []
            if not paragraphs:
                levels.append((1, chunk)) # Fallback al chunk de página
            
            for p in paragraphs:
                levels.append((2, p)) # Nivel 2: Párrafos
            
            for j, (nivel, fragment) in enumerate(levels):
                try:
                    vec = self.embedder.encode(fragment).tolist()
                except Exception:
                    continue
                
                payload = {
                    "text": fragment,
                    "document": doc_id,
                    "session_id": collection_id, # Usamos el ID de colección aquí
                    "tema": tema_actual,
                    "subtema": subtema_actual,
                    "nivel": nivel,
                    "page_number": page_num
                }
                points.append(PointStruct(id=str(uuid.uuid4()), vector=vec, payload=payload))

            if points and (len(points) > 50 or i == total_pages - 1): # Subir en lotes
                upsert_points(collection, points)
                points.clear()
        
        if points: # Asegurarse de subir los puntos restantes
            upsert_points(collection, points)
            points.clear()


    # =======================
    # 🔹 Búsqueda avanzada
    # =======================
    def search(
        self,
        collection_id: str, # ID de colección global o de sesión
        query: str,
        top_k: int = 5,
        use_hyde: bool = True,
        use_bm25: bool = False,
        use_semantic: bool = True,
        filters: Optional[Dict[str, Any]] = None 
    ) -> List[dict]:
        
        # Modificación: Ya no listamos colecciones, usamos la que nos pasan
        relevant_collection = self._collection_name(collection_id, None) # Asumimos tema general
        if not collection_exists(relevant_collection):
             # Fallback por si la colección 'general' no existe pero otras sí
             all_collections = list_collections()
             relevant_prefix = collection_id
             if "knowledge_" not in relevant_prefix:
                 relevant_prefix = f"knowledge_{collection_id}"

             relevant = [c for c in all_collections if c.startswith(relevant_prefix)]
             if not relevant:
                 print(f"Advertencia: No se encontró ninguna colección para '{collection_id}'")
                 return []
             relevant_collection = relevant[0] # Solo buscamos en la primera encontrada
             print(f"Advertencia: Colección '{relevant_collection}' no encontrada, usando '{relevant_collection}' como fallback.")


        # Lógica de HyDE
        query_text = query
        if use_hyde:
            try:
                hyp = self.openai.chat.completions.create(
                    model=self.hyde_model,
                    messages=[
                        {"role": "system", "content": (
                            "Eres un ayudante que reformula preguntas para mejorar la búsqueda "
                            "en una base de conocimiento interna. No inventes hechos ni añadas "
                            "información externa, solo reformula con sinónimos o detalle útil."
                        )},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=200,
                    temperature=0.25
                )
                query_text = hyp.choices[0].message.content.strip() or query
            except Exception:
                query_text = query

        # Lógica de Encode
        try:
            q_vector = self.embedder.encode(query_text).tolist()
        except Exception:
            q_vector = self.embedder.encode(query).tolist()


        combined_results: List[dict] = []
        
        q_filter = filters if filters else None
        if q_filter:
            print(f"Filtrando búsqueda con: {q_filter}")

        # Buscamos solo en la colección relevante
        results = search_similar(relevant_collection, q_vector, limit=top_k, filters=q_filter)
        
        for r in results:
            payload = getattr(r, "payload", {}) or {}
            text = payload.get("text", "")
            nivel = int(payload.get("nivel", 2))
            score = getattr(r, "score", 0.0)
            weighted = score * self.nivel_pesos.get(nivel, 1.0)
            
            combined_results.append({
                "text": text,
                "score": weighted,
                "tema": payload.get("tema"),
                "subtema": payload.get("subtema"),
                "document": payload.get("document"),
                "page_number": payload.get("page_number")
            })

        combined_results.sort(key=lambda x: x["score"], reverse=True)
        return combined_results[:top_k]