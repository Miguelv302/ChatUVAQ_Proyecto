# backend/ingest.py
import os
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# Importamos las clases y funciones de nuestra app
from app.qdrant_helper import qdrant_client
from app.rag_engine import RAGEngine
from app.utils import OPENAI_API_KEY, QDRANT_URL, CHUNK_SIZE
from app.parser import extract_chunks_from_pdf, extract_chunks_from_docx

# --- Configuración ---
# El ID de la colección global donde vivirá TODO el conocimiento
UVAQ_COLLECTION_ID = "uvaq_main_knowledge"
# La carpeta donde pusiste tus archivos
SOURCE_DIRECTORY = "documentos_fuente"

def run_ingestion():
    print("Iniciando motor de RAG...")
    embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    engine = RAGEngine(qdrant_client, embedder, openai_client, chunk_size=CHUNK_SIZE)
    
    # Aseguramos que la colección global exista
    engine.ensure_collection(UVAQ_COLLECTION_ID)
    
    print(f"Buscando documentos en: {SOURCE_DIRECTORY}")
    
    for filename in os.listdir(SOURCE_DIRECTORY):
        file_path = os.path.join(SOURCE_DIRECTORY, filename)
        
        if not os.path.isfile(file_path):
            continue
            
        print(f"\nProcesando archivo: {filename}")
        chunks = []
        
        try:
            if filename.lower().endswith(".pdf"):
                chunks = extract_chunks_from_pdf(file_path, filename)
            elif filename.lower().endswith(".docx"):
                chunks = extract_chunks_from_docx(file_path, filename)
            else:
                print(f"Saltando archivo no soportado: {filename}")
                continue
                
            if chunks:
                print(f"Indexando {len(chunks)} chunks de '{filename}' en Qdrant (Colección: {UVAQ_COLLECTION_ID})...")
                # Usamos el ID global para indexar
                engine.index_document_chunks(UVAQ_COLLECTION_ID, chunks, document_id=filename)
                print(f"'{filename}' indexado exitosamente.")
            else:
                print(f"No se extrajo texto de '{filename}'.")
                
        except Exception as e:
            print(f"Error fatal procesando '{filename}': {e}")

    print("\n✅ Proceso de ingesta completado.")

if __name__ == "__main__":
    run_ingestion()