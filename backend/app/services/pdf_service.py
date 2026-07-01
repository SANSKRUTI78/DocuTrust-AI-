import os
import fitz  # PyMuPDF
import pdfplumber
from typing import List, Dict
import re

def extract_text_from_pdf(file_path: str) -> Dict:
    """Extract text, metadata, and structure from PDF."""
    result = {
        "pages": [],
        "total_pages": 0,
        "metadata": {},
        "full_text": ""
    }
    
    try:
        # Use PyMuPDF for fast extraction
        doc = fitz.open(file_path)
        result["total_pages"] = len(doc)
        result["metadata"] = doc.metadata
        
        all_text = []
        for page_num, page in enumerate(doc, 1):
            text = page.get_text("text")
            blocks = page.get_text("dict")["blocks"]
            
            page_data = {
                "page_number": page_num,
                "text": text,
                "word_count": len(text.split()),
            }
            result["pages"].append(page_data)
            all_text.append(text)
        
        result["full_text"] = "\n\n".join(all_text)
        doc.close()
        
    except Exception as e:
        # Fallback to pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                result["total_pages"] = len(pdf.pages)
                all_text = []
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    result["pages"].append({"page_number": page_num, "text": text})
                    all_text.append(text)
                result["full_text"] = "\n\n".join(all_text)
        except Exception as e2:
            raise Exception(f"PDF extraction failed: {e2}")
    
    return result

def chunk_text(pages: List[Dict], chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """Split pages into overlapping chunks."""
    chunks = []
    chunk_id = 0
    
    for page_data in pages:
        text = page_data["text"].strip()
        if not text:
            continue
        
        words = text.split()
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            if len(chunk_words) < 30:
                continue
            
            chunks.append({
                "chunk_index": chunk_id,
                "content": " ".join(chunk_words),
                "page_number": page_data["page_number"],
                "word_count": len(chunk_words),
            })
            chunk_id += 1
    
    return chunks
