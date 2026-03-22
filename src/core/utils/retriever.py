import faiss
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

from src.core.utils.paths import get_faiss_index_path, get_faiss_metadata_path
from src.core.utils.processor import embedding_dim

# --- Logger Setup ---
logger = logging.getLogger(__name__)

_cached_index = None
_cached_metadata = None
_cached_mtime = 0.0

def retrieve_similar(
    query_embeddings: List[List[float]],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Performs similarity search for given embeddings and returns top-k matches.

    Args:
        query_embeddings (List[List[float]]): Embedding vectors of query chunks.
        top_k (int): Number of matches to retrieve per chunk.

    Returns:
        List[Dict]: Match metadata including distance and index info.
    """
    if not query_embeddings:
        logger.warning("[Retriever] No embeddings provided for retrieval.")
        return []

    index_path = get_faiss_index_path()
    metadata_path = get_faiss_metadata_path()

    if not index_path.exists():
        raise FileNotFoundError(f"[Retriever] FAISS index missing: {index_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"[Retriever] Metadata file missing: {metadata_path}")

    try:
        global _cached_index, _cached_metadata, _cached_mtime
        
        current_mtime = index_path.stat().st_mtime
        if _cached_index is None or current_mtime != _cached_mtime:
            _cached_index = faiss.read_index(str(index_path))
            with metadata_path.open("r", encoding="utf-8") as f:
                _cached_metadata = json.load(f)
            _cached_mtime = current_mtime
            
        index = _cached_index
        metadata = _cached_metadata
        
        expected_dim = embedding_dim

        # Prepare query
        query_array = np.array(query_embeddings, dtype=np.float32)
        if query_array.ndim == 1:
            query_array = query_array.reshape(1, -1)

        actual_dim = query_array.shape[1]
        if actual_dim != expected_dim:
            raise ValueError(f"[Retriever] Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}")

        # Perform search
        D, I = index.search(query_array, top_k)

        # Collect results
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
