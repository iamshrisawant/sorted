# builder.py

import json
import logging
from pathlib import Path
from typing import List

# The builder now imports the single master function from the processor
from src.core.utils.processor import process_file
from src.core.utils.indexer import index_file
from src.core.utils.paths import (
    get_config_file,
    get_faiss_index_path,
    get_faiss_metadata_path,
    get_organized_paths,
)

# --- Logger Setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


# --- Internal Helpers ---
def is_valid_file(file_path: Path) -> bool:
    return (
        file_path.is_file()
        and not file_path.name.startswith("~")
        and not file_path.name.startswith(".")
    )


def read_config() -> dict:
    path = get_config_file()
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def update_config(updates: dict) -> None:
    path = get_config_file()
    config = read_config()
    config.update(updates)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# --- Core Builder Logic ---
def process_folder(folder_path: str) -> None:
    folder = Path(folder_path).resolve()
    if not folder.exists() or not folder.is_dir():
        logger.warning(f"[Builder] Skipping invalid directory: {folder}")
        return

    logger.info(f"[Builder] Processing folder: {folder}")

    for file_path in folder.rglob("*"):
        if not is_valid_file(file_path):
            continue

        try:
            logger.info(f"[Builder] Found: {file_path.name}")
            
            # Single call to the processor
            processed_data = process_file(file_path)

            # Check if processing was successful and yielded embeddings
            if not processed_data or not processed_data.get("embeddings"):
                logger.warning(f"[Builder] Processing failed or yielded no embeddings for: {file_path.name}")
                continue

            # Pass the processed data directly to the indexer
            index_file(
                embeddings=processed_data["embeddings"],
                file_metadata={
                    "file_path": str(file_path.resolve()),
                    "file_name": processed_data["file_name"],
                    "parent_folder": processed_data["parent_folder"],
                    "parent_folder_path": processed_data["parent_folder_path"],
                    "file_type": processed_data["file_type"],
                    "content_hash": processed_data["content_hash"],
                    "relative_folder": str(file_path.parent.relative_to(folder)).replace('\\', '/')
                },
                faiss_index_path=get_faiss_index_path(),
                metadata_store_path=get_faiss_metadata_path(),
            )

        except Exception as e:
            logger.warning(f"[Builder] Failed to process {file_path.name}: {repr(e)}")


def build_from_paths(paths: List[str]) -> None:
    if not paths:
        logger.error("[Builder] No folder paths provided.")
        return

    logger.info("[Builder] Starting full index rebuild...")
    update_config({"builder_busy": True})

    for folder in paths:
        process_folder(folder)

    update_config({"builder_busy": False, "faiss_built": True})
    logger.info("[Builder] Index build complete.")


if __name__ == "__main__":
    build_from_paths(get_organized_paths())