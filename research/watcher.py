import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer
import config
from sorter import SemantiSorter

class DebouncedHandler(FileSystemEventHandler):
    def __init__(self, sorter):
        self.sorter = sorter
        self.pending_timers = {}

    def on_created(self, event):
        if event.is_directory:
            return
        self.process_with_debounce(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self.process_with_debounce(event.src_path)

    def process_with_debounce(self, file_path):
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in config.SUPPORTED_EXTENSIONS:
            return

        # Cancel existing timer if present
        if file_path in self.pending_timers:
            self.pending_timers[file_path].cancel()

        # Start new timer (Debounce: 1 second)
        print(f"Detected {filename}, waiting 1s for write completion...")
        timer = Timer(1.0, self.safe_sort, [file_path])
        self.pending_timers[file_path] = timer
        timer.start()

    def safe_sort(self, file_path):
        # Remove from pending
        if file_path in self.pending_timers:
            del self.pending_timers[file_path]
        
        # Check if file still exists (might have been moved/deleted)
        if os.path.exists(file_path):
            try:
                self.sorter.sort_file(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    print(f"Initializing SemantiSort Watcher...")
    print(f"Monitoring: {config.SOURCE_DIR}")
    
    # Initialize Sorter (loads models)
    sorter = SemantiSorter()
    
    event_handler = DebouncedHandler(sorter)
    observer = Observer()
    observer.schedule(event_handler, config.SOURCE_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
