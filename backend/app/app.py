# backend/app/app.py
import os
import uuid
import re
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from typing import List, Dict, Any, Tuple
from collections import Counter
from pydantic import BaseModel
import io

# Importamos las clases y funciones de nuestra app
from .utils import OPENAI_API_KEY, QDRANT_URL, RAG_MODE, CHUNK_SIZE
from .qdrant_helper import qdrant_client
from .rag_engine import RAGEngine

# ==========================
# 🔧 Inicialización
# ==========================

# El ID de la colección global que creó ingest.py
UVAQ_COLLECTION_ID = "uvaq_main_knowledge"

embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
engine = RAGEngine(qdrant_client, embedder, openai_client, chunk_size=CHUNK_SIZE)

app = FastAPI()

# --- Configuración de CORS ---
origins = [
    "http://localhost:3000", # React (CRA)
    "http://localhost:5173", # React (Vite)
    # Añade la URL de tu frontend en producción
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sesiones en memoria (para historial de chat)
sessions = {} 

# --- Modelos Pydantic ---
class ChatMessage(BaseModel):
    message: str

# --- Funciones auxiliares de lógica de chat ---
def parse_metadata_query(message: str) -> Tuple[Dict[str, Any], str]:
    filters = {}
    query_para_vector = message
    match_page = re.search(r"(?i)(en la |de la )?p[aá]gina\s+([0-9]+)", message)
    if match_page:
        filters["page_number"] = int(match_page.group(2))
        return filters, message 
    
    match_key = re.search(r"(?i)(?:tema|cap[ií]tulo|subtema|secci[oó]n)\s+([0-9]+(?:\.[0-9]+)*)", message)
    if match_key:
        clave = match_key.group(1) 
        parts = clave.split('.')
        if len(parts) == 2: filters["tema"] = clave
        elif len(parts) > 2: filters["subtema"] = clave
        else: filters["tema"] = clave
        return filters, message
    return filters, query_para_vector


def update_session_focus(session: dict, results: List[Dict]):
    if not results: return
    doc_counts = Counter([res.get("document") for res in results])
    top_doc, count = doc_counts.most_common(1)[0]
    if top_doc and count / len(results) > 0.6:
        if session.get("current_focus") != top_doc:
            session["current_focus"] = top_doc
    else:
        if session.get("current_focus") is not None:
            session["current_focus"] = None

# ==========================
# 🚀 ENDPOINTS DE API
# ==========================

# Función de ayuda para inicializar sesión
def init_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = {
            "name": f"Chat {len(sessions)+1}", 
            "history": [], 
            "current_focus": None 
        }

@app.post("/api/chat/{session_id}", response_class=JSONResponse)
async def api_chat_endpoint(
    session_id: str,
    user_message: ChatMessage,
    message_pdf: str = Query(None) # Aún podemos filtrar por documento
):
    """
    Recibe un mensaje de chat, ejecuta el RAG y devuelve la respuesta.
    """
    init_session(session_id)
    session = sessions[session_id]
    message = user_message.message
    selected_pdf = message_pdf
    answer = None

    try:
        # -------------------
        # 🔹 INTENCIÓN 2: Preguntas Triviales
        # -------------------
        trivial_keywords = ["hola", "buenos días", "cómo te llamas", "quién eres"]
        if not answer and any(keyword in message.lower() for keyword in trivial_keywords):
            if "hola" in message.lower() or "buenos días" in message.lower():
                 answer = "¡Hola! Soy tu asistente virtual de la UVAQ. ¿En qué te puedo ayudar?"
            else:
                 answer = "Soy un asistente virtual de la UVAQ. Mi propósito es responder preguntas basadas *únicamente* en la información oficial de la universidad."

        # -------------------
        # 🔹 INTENCIÓN 3: Búsqueda RAG
        # -------------------
        if not answer: 
            use_bm25 = RAG_MODE in ("hybrid", "all", "all", "hybrid+hyde")
            use_semantic = True
            use_hyde = RAG_MODE in ("hyde", "all", "hybrid+hyde")
            filters, query_para_vector = parse_metadata_query(message)
            
            if selected_pdf:
                filters["document"] = selected_pdf
                if session.get("current_focus") != selected_pdf:
                        session["current_focus"] = selected_pdf
            elif not filters:
                current_focus = session.get("current_focus")
                if current_focus:
                    filters["document"] = current_focus
            
            # --- ¡CAMBIO CLAVE! ---
            # Buscamos siempre en la colección global
            results = engine.search(
                UVAQ_COLLECTION_ID, # <-- ID Global
                query=query_para_vector, top_k=6,
                use_bm25=use_bm25, use_semantic=use_semantic, use_hyde=use_hyde,
                filters=filters
            )
            
            if not filters.get("document"):
                update_session_focus(session, results)
            
            if results:
                # El resto de la lógica de OpenAI se queda 100% igual
                context_parts = [f"Fuente: {r.get('document', '?')} (Grupo {r.get('page_number', '?')}):\n{r['text']}" for r in results]
                ctx = "\n\n---\n\n".join(context_parts)
                metaprompt = f"""
Eres un asistente experto de la UVAQ. Responde en español usando únicamente la información proporcionada.
REGLAS ESTRICTAS:
1. Basa tu respuesta *solo* en las fuentes de contexto.
2. Si la información es contradictoria, señálalo.
3. Si la información es complementaria, sintetízala.
4. Formatea la respuesta en Markdown.
5. Si la información no es suficiente, di "No tengo información sobre ese tema en los documentos oficiales."
---
Pregunta del Usuario: {message}
---
Contexto de los Documentos: {ctx}
---
Tu Respuesta:
"""
                resp = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Eres un asistente experto de la UVAQ que solo usa las fuentes proporcionadas."},
                        {"role": "user", "content": metaprompt}
                    ],
                    max_tokens=700, temperature=0.1
                )
                answer = resp.choices[0].message.content.strip()
            else:
                answer = "No tengo información sobre ese tema en los documentos oficiales."

        session["history"].append(("Tú", message))
        session["history"].append(("Bot", answer))
        
        return {"sender": "Bot", "message": answer, "focus": session.get("current_focus")}
    
    except Exception as e:
        print(f"Error en api_chat_endpoint: {e}")
        return JSONResponse(status_code=500, content={"sender": "Bot", "message": f"Error del servidor: {e}"})

@app.get("/health")
async def health_check():
    """Verifica que el API esté viva."""
    return {"status": "ok"}