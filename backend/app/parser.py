# backend/app/parser.py
import fitz  # PyMuPDF
import docx
from docx.document import Document
from typing import List, Dict, Any
import io

def extract_chunks_from_pdf(file_path: str, filename: str) -> List[dict]:
    """Extrae texto de un PDF en el disco."""
    chunks = []
    try:
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                if text.strip():
                    chunks.append({
                        "text_content": text,
                        "page_number": page_num + 1,
                        "source_document": filename
                    })
        return chunks
    except Exception as e:
        print(f"Error extrayendo PDF {filename}: {e}")
        return []

def extract_chunks_from_docx(file_path: str, filename: str) -> List[dict]:
    """Extrae texto de un DOCX en el disco."""
    chunks = []
    try:
        doc: Document = docx.Document(file_path)
        page_text = ""
        page_num = 1
        paragraphs_on_page = 0
        
        for para in doc.paragraphs:
            if para.text.strip():
                page_text += para.text + "\n\n"
                paragraphs_on_page += 1
            
            is_heading = para.style.name.startswith('Heading')
            
            if (paragraphs_on_page >= 10 or (is_heading and page_text.strip())) and page_text.strip():
                chunks.append({
                    "text_content": page_text,
                    "page_number": page_num,
                    "source_document": filename
                })
                page_num += 1
                page_text = ""
                paragraphs_on_page = 0

        if page_text.strip():
            chunks.append({
                "text_content": page_text,
                "page_number": page_num,
                "source_document": filename
            })
    except Exception as e:
        print(f"Error extrayendo DOCX {filename}: {e}")
        return []
    
    return chunks