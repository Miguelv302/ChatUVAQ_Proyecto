# backend/app/main.py
import os
import io
import logging
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import fitz        # pdf extract
import docx        # docx extract

from app.utils import CHUNK_SIZE, ADMIN_TOKEN, LLAMA_MODEL, LLMSTUDIO_URL
from app.qdrant_helper import qdrant_client
from app.rag_engine import RAGEngine
from app.embedder_llama import LlamaEmbedder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Colección global usada tanto por admin como por usuario
GLOBAL_COLLECTION = "knowledge_global"

# Inicializar componentes principales
embedder = LlamaEmbedder()
engine = RAGEngine(
    qdrant_client,
    embedder=embedder,
    chunk_size=CHUNK_SIZE,
    multi_collection=False,
)

app = FastAPI(title="UVAQ Chatbot - Backend")

# -------------------------
# Modelos
# -------------------------
class ChatMessage(BaseModel):
    message: str


# -------------------------
# Extractores de PDF y DOCX
# -------------------------
def extract_chunks_from_pdf_bytes(file_bytes: bytes, filename: str) -> List[dict]:
    chunks = []
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for i, page in enumerate(doc):
                text = page.get_text("text")
                if text and text.strip():
                    chunks.append({
                        "text_content": text,
                        "page_number": i + 1,
                        "source_document": filename
                    })
    except Exception as e:
        logger.error(f"Error extrayendo PDF {filename}: {e}")
    return chunks


def extract_chunks_from_docx_bytes(file_bytes: bytes, filename: str) -> List[dict]:
    chunks = []
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        CHAR_THRESHOLD = 1800
        current_block = ""
        index = 1

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Detectar headings si existen
            is_heading = False
            try:
                is_heading = para.style.name.startswith("Heading")
            except Exception:
                pass

            if is_heading and current_block.strip():
                chunks.append({
                    "text_content": current_block,
                    "page_number": index,
                    "source_document": filename
                })
                index += 1
                current_block = text + "\n\n"

            elif len(current_block) + len(text) > CHAR_THRESHOLD:
                chunks.append({
                    "text_content": current_block,
                    "page_number": index,
                    "source_document": filename
                })
                index += 1
                current_block = text + "\n\n"

            else:
                current_block += text + "\n\n"

        # Ultimo bloque
        if current_block.strip():
            chunks.append({
                "text_content": current_block,
                "page_number": index,
                "source_document": filename
            })

    except Exception as e:
        logger.error(f"Error extrayendo DOCX {filename}: {e}")

    return chunks


# =========================================================
#  ADMIN – CARGA DE DOCUMENTOS (solo .pdf y .docx)
# =========================================================

@app.post("/admin/upload_document")
async def admin_upload_document(
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """
    Endpoint para cargar documentos por el administrador.
    Solo PDF y DOCX.
    Requiere:  Header -> Authorization: Bearer <ADMIN_TOKEN>
    """

    # Validar token
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.split(" ", 1)[1].strip()

    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Leer archivo
    filename = file.filename or "uploaded_file"
    content = await file.read()

    # Extraer chunks según tipo de archivo
    if filename.lower().endswith(".pdf"):
        chunks = extract_chunks_from_pdf_bytes(content, filename)

    elif filename.lower().endswith(".docx"):
        chunks = extract_chunks_from_docx_bytes(content, filename)

    else:
        raise HTTPException(
            status_code=400,
            detail="Formato no soportado. Use .pdf o .docx"
        )

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No se pudo extraer texto del documento"
        )

    # Guardar en colección global
    engine.index_document_chunks(GLOBAL_COLLECTION, chunks, document_id=filename)

    return JSONResponse(status_code=200, content={
        "message": f"Documento '{filename}' indexado correctamente",
        "chunks": len(chunks),
    })


# =========================================================
#  USUARIO FINAL – CHAT SOLO TEXTO
# =========================================================

@app.post("/api/chat")
async def chat_user(msg: ChatMessage):
    """
    Chat del usuario final.
    Realiza retrieval, reranking y generación de respuesta.
    """

    query = msg.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Mensaje vacío")

    try:
        # Buscar en embeddings globales
        candidates = engine.retrieve_candidates(
            GLOBAL_COLLECTION,
            query=query,
            top_k=20
        )

        # Rerank con el modelo
        reranked = engine.rerank_candidates(
            query,
            candidates,
            top_n=5
        )

        if not reranked:
            reply = "No encontré información relacionada en los documentos cargados."
        else:
            reply = engine.generate_answer(query, reranked, policy="strict")

        return {"sender": "Bot", "message": reply}

    except Exception as e:
        logger.exception("Error en chat")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
