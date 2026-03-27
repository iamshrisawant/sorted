import json
from pathlib import Path
from typing import List, Union, Dict
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

import os
ROOT_DIR = Path(__file__).resolve().parents[3]
TEST_DIR_ENV = os.environ.get("SORTED_TEST_DATA_DIR")
if TEST_DIR_ENV:
    DATA_DIR = Path(TEST_DIR_ENV)
else:
    DATA_DIR = ROOT_DIR / "src" / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

PATHS_FILE = DATA_DIR / "paths.json"
CONFIG_FILE = DATA_DIR / "config.json"
LOGS_FILE = DATA_DIR / "logs.jsonl"

FAISS_INDEX_FILE = DATA_DIR / "index.faiss"
FAISS_METADATA_FILE = DATA_DIR / "index_meta.jsonl"

from src.core.utils.locking import FileLock

logger = logging.getLogger(__name__)

def normalize_path(p: Union[str, Path]) -> str:
    return str(Path(p).expanduser().resolve())

def get_paths_file() -> Path:
    return PATHS_FILE

def get_config_file() -> Path:
    return CONFIG_FILE

def get_logs_path() -> Path:
    return LOGS_FILE

def get_faiss_index_path() -> Path:
    return FAISS_INDEX_FILE

def get_faiss_metadata_path() -> Path:
    return FAISS_METADATA_FILE

def get_data_dir() -> Path:
    return DATA_DIR

def get_unsorted_folder() -> Path:
    return Path.home() / "Documents" / "sortedpc" / "unsorted"

def get_xml() -> Path:
    return ROOT_DIR / "src" / "config.xml"

def get_project_root_for_imports() -> Path:
    return ROOT_DIR.parent.parent.parent.parent


def get_watcher_log() -> Path:
    return ROOT_DIR / "src" / "watcher_launch.log"

def get_watch_paths() -> List[str]:
    return _load_list_from_json(PATHS_FILE, "watch_paths")

def get_organized_paths() -> List[str]:
    return _load_list_from_json(PATHS_FILE, "organized_paths")

def get_builder_state() -> bool:
    return _load_config_flag("builder_busy")

def get_faiss_state() -> bool:
    return _load_config_flag("faiss_built")

def get_watcher_state() -> bool:
    return _load_config_flag("watcher_online")

def get_scoring_weights() -> Dict[str, float]:
    return _load_dict_from_json(CONFIG_FILE, keys=["alpha", "beta", "gamma", "delta"])

def load_all_logs() -> List[Dict]:
    if not LOGS_FILE.exists():
        return []
    try:
        with LOGS_FILE.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    except (IOError, PermissionError, json.JSONDecodeError):
        return []

def get_move_logs() -> Dict[str, Dict]:
    logs = load_all_logs()
    return {
        log["file_path"]: log for log in logs if log.get("category", "moves") == "moves"
    }

def get_correction_logs() -> Dict[str, Dict]:
    logs = load_all_logs()
    return {
        log["file_path"]: log for log in logs if log.get("category") == "corrections"
    }

def _load_list_from_json(path: Path, key: str) -> List[str]:
    if not path.exists():
        return []
    try:
        with FileLock(path):
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return [normalize_path(p) for p in data.get(key, [])]
    except (IOError, PermissionError, json.JSONDecodeError):
        return []

def _load_dict_from_json(path: Path, keys: List[str]) -> Dict[str, float]:
    if not path.exists():
        return {k: 0.0 for k in keys}
    try:
        with FileLock(path):
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: float(data.get(k, 0.0)) for k in keys}
    except (IOError, PermissionError, json.JSONDecodeError):
        return {k: 0.0 for k in keys}

def _load_config_flag(key: str) -> bool:
    if not CONFIG_FILE.exists():
        return False
    try:
        with FileLock(CONFIG_FILE):
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                config = json.load(f)
            return bool(config.get(key, False))
    except (IOError, PermissionError, json.JSONDecodeError):
        return False

def update_config(updates: Dict) -> None:
    """Thread-safe update of config.json"""
    _update_json_file(CONFIG_FILE, updates)

def update_paths(updates: Dict) -> None:
    """Thread-safe update of paths.json"""
    _update_json_file(PATHS_FILE, updates)

def _update_json_file(path: Path, updates: Dict) -> None:
    try:
        with FileLock(path):
            data = {}
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            
            data.update(updates)
            
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
    except (IOError, PermissionError, json.JSONDecodeError) as e:
        logger.error(f"Failed to update {path.name}: {e}")
