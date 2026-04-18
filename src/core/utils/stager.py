import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from src.core.utils.paths import normalize_path, get_data_dir
from src.core.utils.locking import FileLock

logger = logging.getLogger(__name__)

def get_review_queue_path() -> Path:
    return get_data_dir() / "review_queue.jsonl"

def add_to_review(file_path: str, reason: str, suggestions: Optional[List[str]] = None):
    queue_file = get_review_queue_path()
    file_path = normalize_path(file_path)
    
    new_entry = {
        "file_path": file_path,
        "file_name": Path(file_path).name,
        "reason": reason,
        "suggestions": suggestions or [],
        "timestamp": datetime.now().isoformat()
    }
    
    with FileLock(queue_file):
        existing = _load_queue_internal(queue_file)
        # Prevent duplicates
        if any(item["file_path"] == file_path for item in existing):
            return
            
        existing.append(new_entry)
        with queue_file.open("w", encoding="utf-8") as f:
            for item in existing:
                f.write(json.dumps(item) + "\n")
    
    logger.info(f"[Stager] Added file to manual review queue: {Path(file_path).name} (Reason: {reason})")

def get_review_queue() -> List[Dict]:
    return _load_queue_internal(get_review_queue_path())

def remove_from_review(file_path: str):
    queue_file = get_review_queue_path()
    file_path = normalize_path(file_path)
    
    with FileLock(queue_file):
        existing = _load_queue_internal(queue_file)
        filtered = [item for item in existing if item["file_path"] != file_path]
        
        with queue_file.open("w", encoding="utf-8") as f:
            for item in filtered:
                f.write(json.dumps(item) + "\n")

def _load_queue_internal(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    except (json.JSONDecodeError, IOError):
        return []
