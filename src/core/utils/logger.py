import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

from src.core.utils.paths import get_logs_path
from src.core.utils.locking import FileLock

logger = logging.getLogger(__name__)

def _load_existing_logs(
    log_file: Path,
    target_file_path: str,
    category_to_replace: Optional[str] = None
) -> List[dict]:
    entries = []
    if not log_file.exists():
        return entries

    target_file_path = str(Path(target_file_path).resolve())

    try:
        with log_file.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if not (
                        entry.get("file_path") == target_file_path and
                        entry.get("category") == category_to_replace
                    ):
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except (IOError, PermissionError) as e:
        logger.warning(f"Failed to read existing logs (non-fatal): {e}")
    return entries

def log_move(sorted_data: dict, log_file: Optional[Path] = None):
    log_file = log_file or get_logs_path()
    file_path = str(Path(sorted_data["file_path"]).resolve())

    new_entry = {
        "category": "moves",
        "file_path": file_path,
        "file_name": sorted_data["file_name"],
        "file_type": sorted_data["file_type"],
        "content_hash": sorted_data.get("content_hash", ""),
        "final_folder": str(Path(sorted_data["final_folder"]).resolve()),
        "similar_folders": sorted_data.get("similar_folders", []),
        "scoring_breakdown": sorted_data.get("scoring_breakdown", {}),
        "timestamp": datetime.now().isoformat()
    }

    with FileLock(log_file):
        # We still need to filter out duplicates if we want to "replace" instead of just appending
        # But for moves, maybe we just append? The existing logic was replacing.
        # Let's keep the "replace" logic but optimize it.
        log_entries = _load_existing_logs(log_file, file_path, category_to_replace="moves")
        log_entries.append(new_entry)

        with log_file.open("w", encoding="utf-8") as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")

    logger.info(f"[Logger] Logged system move for {file_path}")

def log_correction(file_path: str, corrected_folder: str, log_file: Optional[Path] = None):
    log_file = log_file or get_logs_path()
    file_path = str(Path(file_path).resolve())
    corrected_folder = str(Path(corrected_folder).resolve())

    new_entry = {
        "category": "corrections",
        "file_path": file_path,
        "file_name": Path(file_path).stem,
        "file_type": Path(file_path).suffix.lstrip("."),
        "final_folder": corrected_folder,
        "similar_folders": [],
        "scoring_breakdown": {},
        "timestamp": datetime.now().isoformat()
    }

    with FileLock(log_file):
        log_entries = _load_existing_logs(log_file, file_path, category_to_replace="corrections")
        log_entries.append(new_entry)

        with log_file.open("w", encoding="utf-8") as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")

    logger.info(f"[Logger] Logged correction for {file_path}")

def has_been_handled(file_path: str, content_hash: Optional[str] = None) -> bool:
    log_file = get_logs_path()
    if not log_file.exists():
        return False

    file_path = str(Path(file_path).resolve())

    try:
        with log_file.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("category") in {"moves", "corrections"}:
                        logged_path = str(Path(entry.get("file_path", "")).resolve())
                        if logged_path == file_path:
                            return True
                        if content_hash and entry.get("content_hash") == content_hash:
                            return True
                except json.JSONDecodeError:
                    continue
    except (IOError, PermissionError):
        return False
    return False

def get_latest_log_entry(file_path: str) -> Optional[Dict]:
    log_file = get_logs_path()
    if not log_file.exists():
        return None

    file_name = Path(file_path).name

    try:
        with log_file.open("r", encoding="utf-8") as f:
            # We don't read all into memory if we can avoid it, but for a small log it's okay.
            # However, for safety and efficiency, let's keep it consistent.
            lines = [
                json.loads(line)
                for line in f
                if line.strip()
            ]

        for entry in reversed(lines):
            if entry.get("file_path", "").endswith(file_name) and entry.get("category") in {"moves", "corrections"}:
                return entry
    except (IOError, PermissionError, json.JSONDecodeError):
        return None
    return None