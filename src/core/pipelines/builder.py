# builder.py

import json
import logging
from pathlib import Path
from typing import List

from src.core.utils.processor import process_file, process_text_context
from src.core.utils.indexer import index_file
from src.core.utils.paths import (
    get_config_file,
    get_faiss_index_path,
    get_faiss_metadata_path,
    get_organized_paths,
    get_folder_contexts,
    update_config,
)
from src.core.utils.notifier import notify_system_event

# --- Logger Setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".csv", ".tsv", 
    ".txt", ".md", ".mdx", ".rst", ".rtf", ".html", ".htm", ".xml", ".eml", ".log"
}

def is_valid_file(file_path: Path) -> bool:
    return (
        file_path.is_file()
        and not file_path.name.startswith("~")
        and not file_path.name.startswith(".")
        and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


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

def process_folder_contexts(paths: List[str]) -> None:
    folder_contexts = get_folder_contexts()
    if not folder_contexts:
        return
        
    for ctx_path_str, text in folder_contexts.items():
        ctx_path = Path(ctx_path_str).resolve()
        
        # Check if this context belongs to one of the paths being built
        is_relevant = False
        relative_folder = "."
        for root_path_str in paths:
            root_path = Path(root_path_str).resolve()
            if root_path in ctx_path.parents or root_path == ctx_path:
                is_relevant = True
                relative_folder = str(ctx_path.relative_to(root_path)).replace('\\', '/')
                break
                
        if not is_relevant:
            continue
            
        logger.info(f"[Builder] Processing folder context for: {ctx_path.name}")
        try:
            processed_data = process_text_context(text, ctx_path)
            if not processed_data or not processed_data.get("embeddings"):
                continue
                
            index_file(
                embeddings=processed_data["embeddings"],
                file_metadata={
                    "file_path": processed_data["file_path"],
                    "file_name": processed_data["file_name"],
                    "parent_folder": processed_data["parent_folder"],
                    "parent_folder_path": processed_data["parent_folder_path"],
                    "file_type": processed_data["file_type"],
                    "content_hash": processed_data["content_hash"],
                    "relative_folder": relative_folder
                },
                faiss_index_path=get_faiss_index_path(),
                metadata_store_path=get_faiss_metadata_path(),
            )
        except Exception as e:
            logger.warning(f"[Builder] Failed to process folder context for {ctx_path_str}: {repr(e)}")

def build_from_paths(paths: List[str]) -> None:
    if not paths:
        logger.error("[Builder] No folder paths provided.")
        return

    logger.info("[Builder] Starting full index rebuild...")
    notify_system_event("Builder", "FAISS Index rebuild started.")
    update_config({"builder_busy": True})

    for folder in paths:
        process_folder(folder)

    process_folder_contexts(paths)

    update_config({"builder_busy": False, "faiss_built": True})
    notify_system_event("Builder", "FAISS Index completely built.")
    logger.info("[Builder] Index build complete.")


if __name__ == "__main__":
    build_from_paths(get_organized_paths())