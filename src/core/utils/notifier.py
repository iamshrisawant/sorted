import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def notify_file_sorted(file_path: str, final_folder: str, similar_folders: list):
    logger.info(f"File sorted: {Path(file_path).name} -> {final_folder}")
    try:
        from plyer import notification
        notification.notify(
            title=f"Sorted: {Path(file_path).name}",
            message=f"Destination: {final_folder}",
            app_name="SortedPC",
            timeout=5
        )
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to send toast notification: {e}")

def notify_system_event(title: str, message: str):
    logger.info(f"System Event: {title} - {message}")
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="SortedPC",
            timeout=5
        )
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Failed to send system event toast: {e}")
