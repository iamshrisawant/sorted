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

def sort_file(processed_data: Dict) -> Dict:
    embeddings = processed_data["embeddings"]
    
    DEPTH_WEIGHT = 0.08
    CONFIDENCE_THRESHOLD = 0.5

    similar_files = retrieve_similar(embeddings)
    if not similar_files:
        logger.info("[Sorter] No similar files found. Using fallback folder.")
        return _build_output(processed_data, str(get_unsorted_folder()), {}, [], used_fallback=True)

    folder_votes = {}
    abs_paths = {}
    
    for rank, match in enumerate(similar_files):
        abs_path = match.get("parent_folder_path")
        rel_folder = match.get("relative_folder")
        if not abs_path: continue
        
        if not rel_folder or rel_folder == ".":
            rel_folder = abs_path
            
        abs_paths[rel_folder] = abs_path
        
        distance = float(match.get("distance", 0.0))
        raw_sim = 1.0 - (distance / 2.0)
        
        decay = math.log2(rank + 2) 
        weighted_score = raw_sim / decay
        
        folder_votes[rel_folder] = folder_votes.get(rel_folder, 0.0) + weighted_score

    final_scores = {}
    scoring_details = {}
    
    best_folder_rel = None
    best_score = -float('inf')

    for rel_folder, knnvote in folder_votes.items():
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

    if best_score < CONFIDENCE_THRESHOLD or best_folder_rel is None:
        logger.info(f"[Sorter] Best score {best_score:.2f} is below threshold {CONFIDENCE_THRESHOLD}.")
        return {
            "file_path": processed_data["file_path"],
            "file_name": processed_data["file_name"],
            "low_confidence": True,
            "suggestions": list(final_scores.keys())[:3] # Top 3 guesses
        }

    best_abs_path = abs_paths[best_folder_rel]
    logger.info(f"[Sorter] Best folder: {Path(best_abs_path).name} | Score: {best_score:.3f}")
    return _build_output(processed_data, best_abs_path, scoring_details, list(final_scores), used_fallback=False)


def __async_sort_callback(processed_data):
    from src.core.utils.stager import add_to_review
    
    # 1. Handle Unextractable (Noise) Files
    if not processed_data or not processed_data.get("embeddings"):
        file_path = processed_data.get("file_path") if processed_data else "Unknown"
        logger.warning(f"[Sorter] No semantic data extracted for {file_path}. Adding to review queue.")
        if processed_data and processed_data.get("file_path"):
            add_to_review(processed_data["file_path"], reason="No semantic data found")
        return

    from src.core.pipelines.watcher import wait_for_builder_release
    if not wait_for_builder_release(timeout=300):
        logger.warning(f"[Sorter] Index locked for too long. Aborting {processed_data.get('file_name')}")
        return

    logger.info(f"[Sorter] Sorting file: {processed_data.get('file_name')}")
    try:
        result = sort_file(processed_data)
        
        # 2. Handle Low Confidence Files
        if result.get("low_confidence"):
            logger.info(f"[Sorter] Low confidence for {result['file_name']}. Staging for review.")
            add_to_review(result["file_path"], reason="Low confidence", suggestions=result.get("suggestions"))
            return

        # 3. Handle High Confidence Files (Auto-Move)
        logger.info(f"[Sorter] Handing off to actor: {processed_data.get('file_name')}")
        from src.core.pipelines.actor import act_on_file
        act_on_file(result)
    except Exception as e:
        logger.error(f"[Sorter] Unhandled exception in sorting pipeline callback: {e}")

def handle_new_file(file_path: str) -> None:
    try:
        logger.info(f"[Sorter] Dispatching file to background workers: {file_path}")
        from src.core.pipelines.worker import bg_engine
        bg_engine.submit_file(file_path, callback=__async_sort_callback)
    except Exception as e:
        logger.error(f"[Sorter] Unhandled exception dispatching file {file_path}: {e}")

if __name__ == "__main__":
    print("Sorter deployed via Paper Mathematics. Boot up main.py to test.")