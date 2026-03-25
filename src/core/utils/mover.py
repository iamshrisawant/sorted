import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def move_file(file_path: str, final_folder: str) -> str:
    src = Path(file_path)
    dst_folder = Path(final_folder)
    dst_folder.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise FileNotFoundError(f"Source file does not exist: {src}")

    dst_path = dst_folder / src.name

    try:
        shutil.move(str(src), str(dst_path))
        logger.info(f"[Mover] Moved {src} -> {dst_path}")
    except Exception as e:
        logger.error(f"[Mover] Failed to move {src} -> {dst_path}: {e}")
        raise

    return str(dst_path)
