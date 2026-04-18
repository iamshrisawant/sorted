import faiss
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.core.utils.paths import get_faiss_index_path, get_faiss_metadata_path
from src.core.utils.processor import embedding_dim

logger = logging.getLogger(__name__)

_cached_index = None
_cached_metadata = None
_cached_mtime = 0.0

def retrieve_similar(
    query_embeddings: List[List[float]],
    top_k: int = 10
) -> Optional[List[Dict[str, Any]]]:
    if not query_embeddings:
        logger.warning("[Retriever] No embeddings provided for retrieval.")
        return []

    index_path = get_faiss_index_path()
    metadata_path = get_faiss_metadata_path()

    if not index_path.exists() or not metadata_path.exists():
        logger.warning("[Retriever] FAISS index or metadata missing. AI is untrained.")
        return None

    try:
        global _cached_index, _cached_metadata, _cached_mtime
        
        from src.core.utils.locking import FileLock
        with FileLock(index_path):
            current_mtime = index_path.stat().st_mtime
            if _cached_index is None or current_mtime != _cached_mtime:
                _cached_index = faiss.read_index(str(index_path))
                with metadata_path.open("r", encoding="utf-8") as f:
                    _cached_metadata = json.load(f)
                _cached_mtime = current_mtime
            
        index = _cached_index
        metadata = _cached_metadata
        
        expected_dim = embedding_dim

        query_array = np.array(query_embeddings, dtype=np.float32)
        if query_array.ndim == 1:
            query_array = query_array.reshape(1, -1)

        actual_dim = query_array.shape[1]
        if actual_dim != expected_dim:
            raise ValueError(f"[Retriever] Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}")

        D, I = index.search(query_array, top_k)

        results = []
        for q_idx, (distances, indices) in enumerate(zip(D, I)):
            for dist, idx in zip(distances, indices):
                if idx == -1 or idx >= len(metadata):
                    continue
                match = metadata[idx].copy()
                match.update({
                    "distance": float(dist),
                    "match_index": idx,
                    "query_chunk": q_idx
                })
                results.append(match)

        logger.info(f"[Retriever] Retrieved {len(results)} matches for {len(query_array)} query chunk(s).")
        return results

    except Exception as e:
        logger.error(f"[Retriever] Retrieval failed: {repr(e)}")
        return []
