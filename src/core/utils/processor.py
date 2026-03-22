import hashlib
import logging
from pathlib import Path
from typing import Dict, Union

import docx
import numpy as np
import pandas as pd
import pdfplumber
from openpyxl import load_workbook
from pptx import Presentation
from sentence_transformers import SentenceTransformer

# --- Logger Setup ---
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

# --- Globals & Constants ---
MODEL_NAME = "all-MiniLM-L6-v2"
_model = None
embedding_dim = 384

def _extract_content(path: Path, file_type: str) -> str:
    """Extracts raw text content from a file."""
    try:
        if file_type == "pdf":
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif file_type == "docx":
            doc = docx.Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        elif file_type == "pptx":
            prs = Presentation(path)
            return "\n".join(shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text"))
        elif file_type == "xlsx":
            wb = load_workbook(path, data_only=True)
            return "\n".join(str(cell.value) for ws in wb.worksheets for row in ws.iter_rows() if cell.value is not None)
        elif file_type == "csv":
            df = pd.read_csv(path)
            return df.astype(str).to_string(index=False)
        elif file_type in ("txt", "md"):
            return path.read_text(encoding="utf-8", errors="ignore")
        else:
            return ""
    except Exception as e:
        logger.error(f"[Processor] Failed to read {path.name} ({file_type}): {e}")
        return ""

def _compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _load_model(local_only: bool = True):
    global _model
    if _model is None:
        try:
            logger.info(f"[Processor] Loading model for the first time: {MODEL_NAME}")
            _model = SentenceTransformer(MODEL_NAME, local_files_only=local_only)
            logger.info("[Processor] Model loaded successfully.")
        except Exception as e:
            logger.error(f"[Processor] Failed to load model: {e}")
            raise e
    return _model

def process_file(file_path: Union[str, Path]) -> Dict:
    """
    PAPER IMPLEMENTATION: Extract First+Last 500 chars (Structural Proxies).
    Generates EXACTLY 1 normalized vector per document.
    """
    path = Path(file_path)
    if not path.is_file():
        return {}
        
    file_type = path.suffix.lower().lstrip('.')
    raw_content = _extract_content(path, file_type)
    
    text = raw_content.strip()
    if len(text) > 1000:
        cleaned_content = text[:500] + "\n...\n" + text[-500:]
    else:
        cleaned_content = text
        
    full_content = f"{path.name}\n{cleaned_content}"
    
    model = _load_model()
    # Normalize embeddings unconditionally so that L2 dist == 2*(1 - cos_sim)
    emb = model.encode(full_content, show_progress_bar=False, normalize_embeddings=True)
    
    if isinstance(emb, np.ndarray):
        embeddings = [emb.tolist()]
    else:
        embeddings = []

    return {
        "file_path": str(path),
        "file_name": path.stem,
        "parent_folder": path.parent.name,
        "parent_folder_path": str(path.parent.resolve()),
        "file_type": file_type,
        "content_hash": _compute_hash(raw_content),
        "embeddings": embeddings,
    }
