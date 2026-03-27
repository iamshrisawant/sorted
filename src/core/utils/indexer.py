import json
import logging
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from src.core.utils.processor import embedding_dim
from src.core.utils.locking import FileLock

logger = logging.getLogger(__name__)

def load_faiss_index(index_path: Path, expected_dim: int) -> faiss.IndexFlatL2:
    if index_path.exists():
        try:
            logger.info(f"[Indexer] Loading existing FAISS index from {index_path.name}")
            index = faiss.read_index(str(index_path))
            if index.d != expected_dim:
                raise ValueError(f"[Indexer] FAISS index dimension mismatch: "
                                 f"expected {expected_dim}, found {index.d}")
            return index
        except Exception as e:
            logger.error(f"[Indexer] Error reading FAISS index: {e}")
            # If corrupted, we might want to return a fresh one, but that's risky. 
            # For now, let it raise or handle it.
            raise

    logger.info(f"[Indexer] Creating new FAISS index with dim={expected_dim}")
    return faiss.IndexFlatL2(expected_dim)

def load_metadata_store(path: Path) -> List[Dict[str, Any]]:
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, PermissionError) as e:
            logger.warning(f"[Indexer] Could not read metadata file: {e}. Starting fresh.")
            return []
    return []

def save_metadata_store(path: Path, metadata: List[Dict[str, Any]]) -> None:
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"[Indexer] Saved metadata to {path.name} ({len(metadata)} entries)")
    except (IOError, PermissionError) as e:
        logger.error(f"[Indexer] Failed to save metadata: {e}")
        raise

def index_file(
    embeddings: List[List[float]],
    file_metadata: Dict[str, str],
    faiss_index_path: Path,
    metadata_store_path: Path
) -> None:
    file_label = file_metadata.get("file_name", "UNKNOWN")

    if not embeddings:
        logger.warning(f"[Indexer] Skipping {file_label}: No embeddings provided.")
        return

    # Use a single lock for both index and metadata to ensure consistency
    lock_path = faiss_index_path.with_suffix(".lock")
    
    try:
        with FileLock(faiss_index_path):
            embedding_array = np.array(embeddings, dtype=np.float32)
            if embedding_array.ndim == 1:
                embedding_array = embedding_array.reshape(1, -1)

            actual_dim = embedding_array.shape[1]
            expected_dim = embedding_dim

            if actual_dim != expected_dim:
                raise ValueError(f"[Indexer] Embedding dim mismatch: expected {expected_dim}, got {actual_dim}")

            index = load_faiss_index(faiss_index_path, expected_dim)

            index.add(embedding_array)
            faiss.write_index(index, str(faiss_index_path))
            logger.info(f"[Indexer] Added {len(embedding_array)} vector(s) for {file_label}")

            metadata = load_metadata_store(metadata_store_path)
            metadata.extend([file_metadata] * len(embedding_array))
            save_metadata_store(metadata_store_path, metadata)

    except Exception as e:
        logger.error(f"[Indexer] Failed to index file: {file_label} | Error: {repr(e)}")
