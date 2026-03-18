import os
import pickle
from sentence_transformers import SentenceTransformer
import config
from utils import extract_text

class DynamicScanner:
    def __init__(self):
        print("Initializing Scanner (Bi-Encoder)...")
        self.model = SentenceTransformer(config.BI_ENCODER_MODEL)
    
    def scan_directory(self, root_path):
        """
        Walks the directory and indexes KEY FEATURES (Filename + Content) 
        as distinct vectors. Does NOT average them.
        Creates the 'Vector Cloud'.
        """
        instances = []
        print(f"Scanning {root_path} to build Vector Cloud...")
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            if dirpath == root_path:
                continue
            
            # Normalize path separators
            rel_path = os.path.relpath(dirpath, root_path).replace('\\', '/')
            valid_files = [f for f in filenames if os.path.splitext(f)[1].lower() in config.SUPPORTED_EXTENSIONS]
            
            if valid_files:
                for fname in valid_files:
                    fpath = os.path.join(dirpath, fname)
                    text = extract_text(fpath)
                    if text:
                        # Encode Filename + Content for maximum semantic signal
                        # Note: extract_text already limits to Smart Context (Header+Footer)
                        full_content = f"{fname}\n{text[:1000]}"
                        emb = self.model.encode(full_content)
                        instances.append({
                            "path": rel_path,
                            "vector": emb,
                            "filename": fname
                        })
            else:
                # Handle empty folders with a virtual anchor
                emb = self.model.encode(os.path.basename(dirpath))
                instances.append({
                    "path": rel_path,
                    "vector": emb,
                    "filename": "virtual_anchor"
                })

        with open(config.INDEX_PATH, 'wb') as f:
            pickle.dump(instances, f)
        print(f"Index built. {len(instances)} vectors saved to {config.INDEX_PATH}")

if __name__ == "__main__":
    scanner = DynamicScanner()
    scanner.scan_directory(config.DEST_DIR)
