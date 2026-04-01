import json
import logging
from pathlib import Path
import shutil

from src.core.utils.paths import (
    get_paths_file,
    get_config_file,
    get_logs_path,
    get_faiss_index_path,
    get_faiss_metadata_path,
    get_unsorted_folder,
    get_data_dir,
)
from src.core.utils.notifier import notify_system_event
# ───────────────────────────────────────────────────────────────

# --- Logger Setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# --- Default Data ---
DEFAULT_PATHS = {"organized_paths": [], "watch_paths": []}
DEFAULT_CONFIG = {"faiss_built": False, "builder_busy": False}

# --- File & Folder Ensurers ---
def ensure_file(path: Path, default_data=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        if path.suffix == ".json":
            path.write_text(json.dumps(default_data or {}, indent=2), encoding="utf-8")
        elif path.suffix == ".jsonl":
            path.write_text("", encoding="utf-8")
        logger.info(f"[Initializer] Created: {path}")

def ensure_unsorted_folder():
    folder = get_unsorted_folder()
    folder.mkdir(parents=True, exist_ok=True)
    logger.info(f"[Initializer] Ensured unsorted folder: {folder}")

def ensure_faiss_files():
    # --- Import `faiss` and `processor` only when needed ---
    import faiss
    from src.core.utils.processor import embedding_dim

    dim = embedding_dim
    index_path = get_faiss_index_path()
    metadata_path = get_faiss_metadata_path()
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    if not index_path.exists():
        logger.info(f"[Initializer] Creating empty FAISS index at: {index_path} (dim={dim})")
        index = faiss.IndexFlatL2(dim)
        faiss.write_index(index, str(index_path))

    ensure_file(metadata_path)

def ensure_ml_models():
    from src.core.utils.paths import get_models_dir
    
    models_dir = get_models_dir()
    # Check if we already have downloaded any models into the cache
    if models_dir.exists() and any(models_dir.iterdir()):
        # We assume the model is downloaded. processor.py will load it using local_files_only=True
        logger.info("[Initializer] ML model verified locally. Skipping network sync for fast startup.")
        return

    from sentence_transformers import SentenceTransformer
    import os
    import warnings
    import logging
    
    try:
        logger.info("[Initializer] Syncing required Machine Learning models to local project cache...")
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            SentenceTransformer("all-MiniLM-L6-v2", cache_folder=str(models_dir), local_files_only=False)
            
        logger.info("[Initializer] ML model verified locally.")
    except Exception as e:
        logger.error(f"[Initializer] FATAL: Could not download the AI weights. Ensure you are connected to the internet or disable VPNs blocking huggingface.co. Error: {e}")

# --- Reset Logic ---
def reset_all():
    logger.warning("[Initializer] Resetting system state...")
    logs_path = get_logs_path()
    if logs_path.exists(): logs_path.unlink()
    data_dir = get_data_dir()
    if data_dir.exists():
        shutil.rmtree(data_dir) # More robust than iterating
    data_dir.mkdir(parents=True, exist_ok=True)
    
    get_paths_file().write_text(json.dumps(DEFAULT_PATHS, indent=2), encoding="utf-8")
    get_config_file().write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    get_logs_path().write_text("", encoding="utf-8")
    ensure_faiss_files()
    logger.info("[Initializer] All system files reset.")

# --- Checks ---
def all_critical_files_exist() -> bool:
    return all([
        get_paths_file().exists(), get_config_file().exists(), get_logs_path().exists(),
        get_faiss_index_path().exists(), get_faiss_metadata_path().exists()
    ])

# --- Initialization Entry ---
def initialize(force_reset: bool = False):
    if force_reset or not all_critical_files_exist():
        logger.warning("[Initializer] Missing critical files or reset forced. Performing full reset...")
        reset_all()
    else:
        ensure_file(get_paths_file(), DEFAULT_PATHS)
        ensure_file(get_config_file(), DEFAULT_CONFIG)
        ensure_file(get_logs_path())
        ensure_faiss_files()
    ensure_unsorted_folder()
    ensure_ml_models()
    logger.info("[Initializer] System initialized.")
    notify_system_event("System Initialized", "SortedPC is ready to use.")

def run_initializer(force_reset: bool = False):
    initialize(force_reset=force_reset)

# --- CLI Entrypoint ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Initialize or reset SortedPC system state.")
    parser.add_argument("--reset", action="store_true", help="Force full reset of all data/config/index files.")
    args = parser.parse_args()
    run_initializer(force_reset=args.reset)
