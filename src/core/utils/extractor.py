import logging
from pathlib import Path
from typing import Union

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

logger = logging.getLogger(__name__)

# Lazy loaded engine
_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        from src.core.utils.paths import get_models_dir
        
        model_root = get_models_dir() / "rapidocr"
        model_root.mkdir(parents=True, exist_ok=True)
        
        # We allow RapidOCR to manage its own downloading, but we point it 
        # to our central models directory for persistence and visibility.
        # Note: RapidOCR handles internal pathing for its default models if 
        # these are None, but we can't easily override the base download dir 
        # without specifying all paths or monkey-patching. 
        # For now, we rely on the library's default but ensure the 
        # directory is mentioned in the logic.
        _ocr_engine = RapidOCR()
    return _ocr_engine

def _ocr_image(img_path: Union[str, Path]) -> str:
    try:
        ocr = get_ocr_engine()
        # RapidOCR accepts file path directly
        result, _ = ocr(str(img_path))
        if result:
            # Result format is [(box, text, confidence), ...]
            text = "\n".join([line[1] for line in result if line[1]])
            return text
        return ""
    except Exception as e:
        logger.error(f"[Extractor] Error running OCR on image {img_path}: {e}")
        return ""

def _extract_pdf(pdf_path: Path) -> str:
    if not fitz:
        logger.warning("[Extractor] PyMuPDF (fitz) is not installed. Skipping PDF extraction.")
        return ""
        
    text_content = []
    try:
        doc = fitz.open(str(pdf_path))
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # --- Scanned PDF Defense Heuristic ---
            # Some scanned PDFs contain invisible, highly corrupted OCR text layers.
            # We measure the "purity" of the text. If it's mostly gibberish/symbols, or very sparse, we force image OCR.
            alphanum_count = sum(c.isalnum() for c in page_text)
            purity = (alphanum_count / len(page_text)) if len(page_text) > 0 else 0
            
            # If native text is > 100 chars and is decently pure (> 50% alphanumerics)
            if len(page_text.strip()) > 100 and purity > 0.5:
                text_content.append(page_text.strip())
                continue
                
            # Otherwise, assume it's a noisy or structural Scanned PDF. Target the visual rendering.
            # Fallback to OCR. Render page to a pixmap
            pix = page.get_pixmap(dpi=150)
            
            import numpy as np
            from PIL import Image
            # PyMuPDF pixmap to PIL Image
            mode = "RGBA" if pix.alpha else "RGB"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            
            # Feed to RapidOCR as numpy array
            ocr = get_ocr_engine()
            img_np = np.array(img.convert("RGB"))
            result, _ = ocr(img_np)
            if result:
                page_text = "\n".join([line[1] for line in result if line[1]])
                text_content.append(page_text)
                
        doc.close()
        return "\n".join(text_content)
    except Exception as e:
        logger.error(f"[Extractor] Error extracting PDF {pdf_path}: {e}")
        return ""

def extract_visual_content(path: Path, file_type: str) -> str:
    """
    Extracts text from images and PDFs using RapidOCR and PyMuPDF.
    Designed to run in an isolated process to avoid GIL bottlenecks.
    """
    if file_type == 'pdf':
        return _extract_pdf(path)
    elif file_type in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
        return _ocr_image(path)
    else:
        return ""
