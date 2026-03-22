# sorter.py

import logging
import math
from pathlib import Path
from typing import Dict, List

from src.core.utils.processor import process_file
from src.core.pipelines.actor import act_on_file
from src.core.utils.paths import get_unsorted_folder
from src.core.utils.retriever import retrieve_similar

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


# --- Format output for actor ---
def _build_output(
    file_data: Dict,
    final_folder: str,
    scoring: Dict[str, Dict],
    candidates: List[str],
    used_fallback: bool = False
) -> Dict:
    return {
        "file_path": file_data["file_path"],
        "file_name": file_data["file_name"],
        "file_type": file_data["file_type"],
        "content_hash": file_data["content_hash"],
        "embeddings": file_data["embeddings"],
        "final_folder": final_folder,
        "scoring_breakdown": scoring,
        "similar_folders": candidates,
        "used_fallback": used_fallback
    }


# --- PAPER IMPLEMENTATION Core Sorting Logic ---
def sort_file(processed_data: Dict) -> Dict:
    """Implement exact paper logic: Rank-Weighted k-NN + Depth Bias + Confidence Gate = 0.5"""
    embeddings = processed_data["embeddings"]
    
    # Paper Parameters
    DEPTH_WEIGHT = 0.08
    CONFIDENCE_THRESHOLD = 0.5

    similar_files = retrieve_similar(embeddings)
    if not similar_files:
        logger.info("[Sorter] No similar files found. Using fallback folder.")
        return _build_output(processed_data, str(get_unsorted_folder()), {}, [], used_fallback=True)

    folder_votes = {}
    abs_paths = {}
    
    # Rank-Weighted K-NN
    # FAISS returns instances pre-sorted by nearest distance
    for rank, match in enumerate(similar_files):
        abs_path = match.get("parent_folder_path")
        rel_folder = match.get("relative_folder")
        if not abs_path: continue
        
        if not rel_folder or rel_folder == ".":
            rel_folder = abs_path
            
        abs_paths[rel_folder] = abs_path
        
        # Recover exact Cosine Similarity from Normalized L2 distance
        distance = float(match.get("distance", 0.0))
        raw_sim = 1.0 - (distance / 2.0)
        
        # Logarithmic Rank Penalization
        decay = math.log2(rank + 2) # rank 0 divides by 1
        weighted_score = raw_sim / decay
        
        folder_votes[rel_folder] = folder_votes.get(rel_folder, 0.0) + weighted_score

    final_scores = {}
    scoring_details = {}
    
    best_folder_rel = None
    best_score = -float('inf')

    for rel_folder, knnvote in folder_votes.items():
        # Depth Bias calculation on strictly relative tree strings
        normalized_path = str(rel_folder).replace('\\', '/')
        depth = len([p for p in normalized_path.strip('/').split('/') if p])
        bias = depth * DEPTH_WEIGHT
        
        final_score = knnvote + bias
        final_scores[rel_folder] = final_score
        
        scoring_details[rel_folder] = {
            "knn_vote": round(knnvote, 4),
            "depth_bias": round(bias, 4),
            "final_score": round(final_score, 4)
        }
        
        if final_score > best_score:
            best_score = final_score
            best_folder_rel = rel_folder

    # The Confidence Gate
    if best_score < CONFIDENCE_THRESHOLD or best_folder_rel is None:
        logger.info(f"[Sorter] Best score {best_score:.2f} is below threshold {CONFIDENCE_THRESHOLD}. Using fallback.")
        return _build_output(processed_data, str(get_unsorted_folder()), scoring_details, list(final_scores), used_fallback=True)

    best_abs_path = abs_paths[best_folder_rel]
    logger.info(f"[Sorter] Best folder: {Path(best_abs_path).name} | Score: {best_score:.3f}")
    return _build_output(processed_data, best_abs_path, scoring_details, list(final_scores), used_fallback=False)


# --- Public Entry Point ---
def handle_new_file(file_path: str) -> None:
    try:
        logger.info(f"[Sorter] Processing new file: {file_path}")
        processed_data = process_file(file_path)

        if not processed_data or not processed_data.get("embeddings"):
            logger.error(f"[Sorter] Aborting sort for {file_path} due to processing failure.")
            return

        logger.info(f"[Sorter] Sorting file: {processed_data.get('file_name')}")
        sorted_data = sort_file(processed_data)

        logger.info(f"[Sorter] Handing off to actor: {processed_data.get('file_name')}")
        act_on_file(sorted_data)

    except Exception as e:
        logger.error(f"[Sorter] Unhandled exception in sorting pipeline for {file_path}: {e}")

if __name__ == "__main__":
    print("Sorter deployed via Paper Mathematics. Boot up main.py to test.")