import logging
from pathlib import Path

try:
    from windows_toasts import Toast, WindowsToaster
    TOASTS_ENABLED = True
except ImportError:
    TOASTS_ENABLED = False

logger = logging.getLogger(__name__)

if TOASTS_ENABLED:
    toaster = WindowsToaster('SortedPC')

def notify_file_sorted(file_path: str, final_folder: str, similar_folders: list):
    logger.info(f"File sorted: {Path(file_path).name} -> {final_folder}")
    if not TOASTS_ENABLED:
        return
    try:
        new_toast = Toast()
        new_toast.text_fields = [f"Sorted: {Path(file_path).name}", f"Destination: {final_folder}"]
        toaster.show_toast(new_toast)
    except Exception as e:
        logger.warning(f"Failed to send toast notification: {e}")

def notify_system_event(title: str, message: str):
    logger.info(f"System Event: {title} - {message}")
    if not TOASTS_ENABLED:
        return
    try:
        new_toast = Toast()
        new_toast.text_fields = [title, message]
        toaster.show_toast(new_toast)
    except Exception as e:
        logger.warning(f"Failed to send system event toast: {e}")
