import logging
from pathlib import Path
from src.core.utils.paths import ROOT_DIR

try:
    from plyer import notification
    TOASTS_ENABLED = True
except ImportError:
    TOASTS_ENABLED = False

logger = logging.getLogger(__name__)

def notify_file_sorted(file_path: str, final_folder: str, similar_folders: list):
    logger.info(f"File sorted: {Path(file_path).name} -> {final_folder}")
    if not TOASTS_ENABLED:
        return
    try:
        notification.notify(
            title=f"Sorted: {Path(file_path).name}",
            message=f"Destination: {final_folder}",
            app_name="SortedPC",
            timeout=5
        )
    except Exception as e:
        logger.warning(f"Failed to send toast notification: {e}")

def notify_system_event(title: str, message: str):
    logger.info(f"System Event: {title} - {message}")
    if not TOASTS_ENABLED:
        return
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="SortedPC",
            timeout=5
        )
    except Exception as e:
        logger.warning(f"Failed to send system event toast: {e}")
