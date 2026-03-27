import os
import time
import logging

try:
    import msvcrt
except ImportError:
    import fcntl

logger = logging.getLogger(__name__)

class FileLock:
    """
    Cross-platform file locking utility for Windows and Unix.
    Used to synchronize access to shared resources like config.json and log files.
    """
    def __init__(self, file_path, timeout=10, delay=0.1):
        self.file_path = str(file_path)
        self.lock_file_path = self.file_path + ".lock"
        self.timeout = timeout
        self.delay = delay
        self.fd = None

    def __enter__(self):
        start_time = time.time()
        while True:
            try:
                # Open the lock file
                self.fd = os.open(self.lock_file_path, os.O_CREAT | os.O_RDWR)
                
                if os.name == 'nt':  # Windows
                    msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)
                else:  # Unix
                    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                return self
            except (IOError, OSError, PermissionError):
                if self.fd is not None:
                    os.close(self.fd)
                    self.fd = None
                
                if time.time() - start_time > self.timeout:
                    logger.error(f"Timeout acquiring lock for: {self.file_path}")
                    raise RuntimeError(f"Timeout acquiring lock for: {self.file_path}")
                
                time.sleep(self.delay)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            try:
                if os.name == 'nt':
                    msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self.fd, fcntl.LOCK_UN)
                os.close(self.fd)
            except Exception as e:
                logger.warning(f"Error releasing lock for {self.file_path}: {e}")
            finally:
                # Try to remove the lock file, but ignore if it's already gone or locked
                try:
                    os.remove(self.lock_file_path)
                except:
                    pass
                self.fd = None
