import sys
import os
import time
import logging
from pathlib import Path

# --- Path Injection ---
try:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
except IndexError:
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

from src.core.utils.paths import (
    get_config_file, 
    get_watch_paths, 
    get_watcher_log,
    get_builder_state,
    get_move_logs,
    normalize_path
)
from src.core.utils.notifier import notify_system_event
from src.core.pipelines.sorter import handle_new_file

# --- Constants ---
SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.pptx', '.xlsx', '.csv', '.txt', '.md'}
SYSTEM_FILES = {'desktop.ini', 'thumbs.db', 'ntuser.dat', 'pictures - shortcut.lnk'}
IGNORE_PREFIXES = ('~', '.', '~$')
TEMP_EXTENSIONS = {'.tmp', '.crdownload', '.part'}

# --- Process Management ---
def is_pid_alive(pid: int) -> bool:
    if pid <= 0: return False
    
    import ctypes
    # PROCESS_QUERY_LIMITED_INFORMATION (0x1000) is enough to check if process exists
    # and is more likely to succeed for processes owned by other users.
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h_process = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if h_process:
        ctypes.windll.kernel32.CloseHandle(h_process)
        return True
    return False

def get_pid_file() -> Path:
    return get_config_file().parent / "watcher.pid"

def write_pid():
    pid_file = get_pid_file()
    try:
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
    except Exception as e:
        logging.getLogger('watcher_debug').error(f"FATAL: Could not write PID file: {e}")
        raise RuntimeError("FATAL: Could not write PID file.")

def clear_pid():
    get_pid_file().unlink(missing_ok=True)


# --- Helper Methods ---
def wait_for_file_ready(file_path: Path, timeout: int = 120) -> bool:
    """
    Prevents WinError 32 crashes by waiting until the OS/Browser 
    releases the file lock. Uses exclusive open attempt for robustness.
    """
    if not file_path.exists():
        return False
        
    # Skip temporary/active download files immediately
    if file_path.suffix.lower() in TEMP_EXTENSIONS:
        return False

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check if file exists and is a file
            if not file_path.is_file():
                return False

            # Check if file size is stable
            size_initial = file_path.stat().st_size
            time.sleep(0.5)
            if not file_path.exists() or file_path.stat().st_size != size_initial:
                continue 
                
            # Attempt to open with exclusive access (O_EXCL not supported on all OS for open, 
            # but on Windows, opening for append/write usually fails if locked)
            # A more robust way on Windows is to try renaming it to itself
            try:
                os.rename(str(file_path), str(file_path))
                return True
            except (OSError, PermissionError):
                pass # Still locked
                
            time.sleep(1)
        except (IOError, PermissionError, OSError):
            time.sleep(1)
            
        if not file_path.exists():
            return False
            
    return False

def wait_for_builder_release(timeout: int = 60) -> bool:
    """
    Prevents C++ Segfaults by pausing the watcher if the main CLI 
    is currently rebuilding the FAISS index.
    """
    start_time = time.time()
    while get_builder_state():
        if time.time() - start_time > timeout:
            return False
        time.sleep(1)
    return True

# --- Event-Driven Handler ---
class InboxEventHandler(FileSystemEventHandler):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        # Cache processed files into memory at startup to fix O(N^2) disk bottleneck
        self.processed_files = set()
        self._lock = threading.Lock()
        self._refresh_processed_files()

    def _refresh_processed_files(self):
        with self._lock:
            try:
                self.processed_files = set(get_move_logs().keys())
            except Exception as e:
                self.logger.warning(f"Failed to load move logs into cache: {e}")

    def process_event(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path).resolve()
        file_name_lower = file_path.name.lower()
        file_ext = file_path.suffix.lower()

        # 1. Strict Path Limitation
        watch_paths = get_watch_paths()
        is_within_allowed = False
        for wp in watch_paths:
            if str(file_path).startswith(wp):
                is_within_allowed = True
                break
        
        if not is_within_allowed:
            # Silently ignore files outside designate paths
            return

        # 2. Filter system and temporary files
        if file_name_lower.startswith(IGNORE_PREFIXES) or file_name_lower in SYSTEM_FILES:
            return
            
        if file_ext in TEMP_EXTENSIONS:
            return

        # 3. Restrict to Supported Text-Based Documents
        if file_ext not in SUPPORTED_EXTENSIONS:
            # Log as unsupported if it's not a known system/temp file we ignore silently
            # But maybe only once per folder scan? For now, just skip silently to avoid log spam
            # based on user request "Only for text based documents".
            return
            
        # Check cache with lock
        with self._lock:
            if str(file_path) in self.processed_files:
                return

        self.logger.info(f"Detected new/supported file: {file_path.name}")
        
        # 4. Wait for the browser/OS to finish writing to the file
        if not wait_for_file_ready(file_path):
            self.logger.warning(f"Timeout waiting for file lock release or unsupported state: {file_path.name}")
            return
            
        # 2. Ensure we don't collide with the FAISS builder
        if not wait_for_builder_release():
            self.logger.warning("FAISS Index is currently locked by the Builder. Aborting sort.")
            return

        try:
            # Double-check cache inside lock just before processing
            with self._lock:
                if str(file_path) in self.processed_files:
                    return
                # Add to local memory cache early to prevent double-triggering
                # If handle_new_file fails, we'll keep it in cache to avoid infinite loops,
                # but maybe we should remove it? Let's keep it for safety.
                self.processed_files.add(str(file_path))

            self.logger.info(f"Delegating to sorter: {file_path.name}")
            handle_new_file(str(file_path))
            
        except Exception as e:
            notify_system_event("Watcher Error", f"Failed to process {file_path.name}")
            self.logger.error(f"ERROR delegating file {file_path.name}: {e}", exc_info=True)
            # Optional: remove from cache on failure if you want to retry?
            # But usually it's better to log and skip than to keep retrying a bad file.

    def on_created(self, event):
        self.process_event(event)
        
    def on_modified(self, event):
        self.process_event(event)

    def on_moved(self, event):
        # Handle files that are downloaded to a .tmp extension and renamed
        if not event.is_directory:
            # Create a mock event for the destination path
            dummy_event = type('Event', (), {'is_directory': False, 'src_path': event.dest_path})()
            self.process_event(dummy_event)


# --- Main Daemon Loop ---
def watcher_loop():
    logger = logging.getLogger('watcher_debug')

    try:
        write_pid()
        logger.info(f"PID {os.getpid()} written successfully. Watcher is online.")
    except RuntimeError as e:
        logger.error(e)
        return

    watch_dirs = get_watch_paths()
    if not watch_dirs:
        logger.warning("No directories configured for watching. Shutting down.")
        clear_pid()
        return

    # Initialize Watchdog Observer
    event_handler = InboxEventHandler(logger)
    observer = Observer()
    
    valid_watches = 0
    for folder_str in watch_dirs:
        folder = Path(folder_str).resolve()
        if folder.is_dir():
            observer.schedule(event_handler, str(folder), recursive=True)
            valid_watches += 1
            
    if valid_watches == 0:
        logger.error("None of the configured watch paths exist. Shutting down.")
        clear_pid()
        return

    observer.start()
    notify_system_event("Watcher Online", "Monitoring via Watchdog events.")
    
    try:
        while True:
            # Main thread sleeps, Watchdog background threads handle I/O events
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        observer.stop()
        observer.join()
        clear_pid()
        notify_system_event("Watcher Offline", "Watcher has stopped.")
        logger.info("Stopped and offline.")


if __name__ == "__main__":
    log_file_path = get_watcher_log()
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger to capture logs from all modules (sorter, processor, etc.)
    # force=True ensures we override any pre-existing configurations from other modules.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_file_path, mode='a', encoding='utf-8')],
        force=True
    )

    # Maintain helper logger for direct watcher logging
    logger = logging.getLogger('watcher_debug')

    try:
        watcher_loop()
    except Exception as e:
        logger.error("A fatal, untrapped error occurred in the watcher's main execution.", exc_info=True)
    finally:
        logger.info("Watcher process has ended.")