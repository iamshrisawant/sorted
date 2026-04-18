import concurrent.futures
import os
import atexit
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class BackgroundSortEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pool = None
            cls._instance.currently_processing = set()
            cls._instance._init_pool()
        return cls._instance
        
    def _init_pool(self):
        # Dynamically allocate CPU cores, max out at 2 or 3 to remain silent in the background
        # Minimum of 1 worker
        cpu_count = os.cpu_count() or 4
        workers = max(1, min(4, cpu_count // 4))
        logger.info(f"[Worker] Initializing Background Engine with {workers} process laborers.")
        self.pool = concurrent.futures.ProcessPoolExecutor(max_workers=workers)
        atexit.register(self.shutdown)
        
    def submit_file(self, file_path: str, callback: Callable[[Any], None] = None):
        """
        Submit a file for processing in the isolated background pool.
        This extracts heavy ML operations away from the watchdog loop.
        """
        try:
            self.currently_processing.add(file_path)
            # We import inside to avoid circular dependencies when starting the pool
            from src.core.utils.processor import process_file
            future = self.pool.submit(process_file, file_path)
            
            if callback:
                # Add a callback to run on the main thread when future completes
                def _done_callback(fut):
                    try:
                        self.currently_processing.discard(file_path)
                        result = fut.result()
                        callback(result)
                    except Exception as e:
                        self.currently_processing.discard(file_path)
                        logger.error(f"[Worker] Exception in isolated process for {file_path}: {e}")
                future.add_done_callback(_done_callback)
            return future
        except Exception as e:
            self.currently_processing.discard(file_path)
            logger.error(f"[Worker] Failed to submit file {file_path} to pool: {e}")
            return None
            
    def shutdown(self):
        if self.pool:
            self.pool.shutdown(wait=False)
            logger.info("[Worker] Background Engine shutdown complete.")

# Global Singleton Engine
bg_engine = BackgroundSortEngine()
