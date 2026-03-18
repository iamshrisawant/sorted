import os
import pypdf
import docx

def extract_text(file_path):
    """
    Robustly extracts text from .txt, .pdf, and .docx files.
    Smart Context: Returns First-500 + Last-500 characters.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = None
    
    try:
        if ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    text = f.read()
        
        elif ext == '.pdf':
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                pages = []
                for page in reader.pages:
                    content = page.extract_text()
                    if content:
                        pages.append(content)
                text = "\n".join(pages)
            
        elif ext == '.docx':
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            
        else:
            return None 

    except Exception as e:
        print(f"[Warning] Failed to read {file_path}: {e}")
        return None

    if text and len(text.strip()) > 0:
        clean_text = text.strip()
        if len(clean_text) > 1000:
            # Smart Context: Header + Footer
            # Using concatenation with separator to avoid word merging
            return clean_text[:500] + "\n...\n" + clean_text[-500:]
        return clean_text
    return None
