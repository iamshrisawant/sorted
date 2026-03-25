

import sys
from pathlib import Path
import os
import time
import logging

try:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
except IndexError:
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.core.utils.paths import get_config_file, get_watch_paths, get_watcher_log
from src.core.utils.notifier import notify_system_event
from src.core.pipelines.sorter import handle_new_file
from src.core.utils.logger import has_been_handled


def is_pid_alive(pid: int) -> bool:
    """Check if a process with the given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def get_pid_file() -> Path:
    """Get the path to the watcher's PID file."""
    return get_config_file().parent / "watcher.pid"

def write_pid():
    """Writes the current process ID to the PID file."""
    pid_file = get_pid_file()
    try:
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
    except Exception as e:
        logging.getLogger('watcher_debug').error(f"FATAL: Could not write PID file: {e}")
        raise RuntimeError("FATAL: Could not write PID file.")

def clear_pid():
    """Removes the PID file on clean shutdown."""
    get_pid_file().unlink(missing_ok=True)


def watcher_loop(poll_interval: float = 3.0):
    logger = logging.getLogger('watcher_debug')

    try:
        write_pid()
        logger.info(f"PID {os.getpid()} written successfully. Watcher is online.")
    except RuntimeError as e:
        logger.error(e)
        return

    notify_system_event("Watcher Online", "Monitoring for new files.")
    
    watch_dirs = get_watch_paths()
    seen_files = set()
    boot_time = time.time()

    try:
        while True:
            for folder_str in watch_dirs:
                folder = Path(folder_str).resolve()
                if not folder.is_dir(): continue

                for file_path in folder.rglob("*"):
                    try:
                        resolved = file_path.resolve()
                        if (not file_path.is_file() or file_path.name.startswith(("~", ".")) or
                            resolved.stat().st_mtime < boot_time or str(resolved) in seen_files or
                            has_been_handled(str(resolved))):
                            continue

                        logger.info(f"Detected: {resolved.name}. Delegating to sorter.")
                        handle_new_file(str(resolved))
                        seen_files.add(str(resolved))
                    except Exception as e:
                        notify_system_event("Watcher Error", f"Failed to process {file_path.name}: {e}")
                        logger.error(f"ERROR delegating file {file_path.name}: {e}", exc_info=True)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        clear_pid()
        notify_system_event("Watcher Offline", "Watcher has stopped.")
        logger.info("Stopped and offline.")


if __name__ == "__main__":
    log_file_path = get_watcher_log()
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    debug_logger = logging.getLogger('watcher_debug')
    debug_logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    debug_logger.addHandler(handler)

    try:
        watcher_loop()
    except Exception as e:
        debug_logger.error("A fatal, untrapped error occurred in the watcher's main execution.", exc_info=True)
    finally:
        debug_logger.info("Watcher process has ended.")
