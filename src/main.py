# [main.py] — Refactored for Improved Workflow and User Experience

import sys
import json
import ctypes
import logging
import subprocess
import time
import os
from pathlib import Path
import shutil
import colorama

# --- Initialize colorama for cross-platform colored output ---
colorama.init(autoreset=True)
from colorama import Fore, Style

# Add project root to path so 'python src/main.py' works
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Application Imports ---
from src.core.pipelines.initializer import run_initializer
from src.core.pipelines.builder import build_from_paths
from src.core.pipelines.actor import handle_correction
from src.core.pipelines.reinforcer import reinforce
from src.core.utils.paths import (
    get_watch_paths, get_organized_paths, get_paths_file,
    get_config_file, get_logs_path, get_xml, ROOT_DIR,
    get_faiss_index_path, get_data_dir
)
from src.core.pipelines.watcher import get_pid_file, is_pid_alive
from src.core.utils.notifier import notify_system_event

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# --- System Constants ---
SYSTEM32_PATH = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32"
SCHTASKS_EXE = SYSTEM32_PATH / "schtasks.exe"
TASKKILL_EXE = SYSTEM32_PATH / "taskkill.exe"
TASK_NAME = "SortedPC_Watcher"
WATCHER_LAUNCHER_BAT = ROOT_DIR / "src" / "launch_watcher.bat"


# ─── Utility Functions ──────────────────────────────────────────────────────

def safe_input(prompt: str = "") -> str:
    """Handles Ctrl+C and EOFError gracefully during input."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print(Fore.YELLOW + "\nExiting.")
        sys.exit(0)

def clear_screen():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    """Prints a formatted header for menus."""
    clear_screen()
    print(Fore.CYAN + "=" * 40)
    print(Style.BRIGHT + f"  {title}".center(40))
    print(Fore.CYAN + "=" * 40 + Style.RESET_ALL)


# ─── Admin and Task Management ──────────────────────────────────────────────

def run_as_admin(command_to_run: str, wait=False):
    """Elevates a command using ShellExecuteW for UAC prompt."""
    try:
        hinstance = ctypes.windll.shell32.ShellExecuteW(None, "runas", command_to_run, None, None, 1)
        if hinstance <= 32:
            print(Fore.RED + "Admin elevation failed or was cancelled.")
            return False
        logger.info(f"Requesting admin rights to run: {command_to_run}")
        return True
    except Exception as e:
        print(Fore.RED + f"Error: Elevation failed. {e}")
        return False

def generate_watcher_launcher_bat() -> bool:
    """Creates a batch file to reliably run the watcher without a console window."""
    try:
        # Prefer pythonw.exe to run without a console window on Windows
        python_dir = Path(sys.executable).parent
        python_exe = python_dir / "pythonw.exe"

        # Fallback to the standard python.exe if pythonw.exe is not found
        if not python_exe.exists():
            python_exe = sys.executable

        watcher_script_path = ROOT_DIR / "src" / "core" / "pipelines" / "watcher.py"
        # The 'start /B' command combined with 'pythonw.exe' ensures the process
        # runs in the background without creating any visible window.
        bat_content = f"""@echo off
set PYTHONPATH={ROOT_DIR}
start "SortedPC Watcher" /B "{python_exe}" "{watcher_script_path}"
"""
        WATCHER_LAUNCHER_BAT.write_text(bat_content)
        return True
    except Exception as e:
        logger.error(f"FATAL: Could not generate watcher launcher script: {e}")
        return False

def do_register_task():
    """Admin: Creates the scheduled task using a generated XML."""
    xml_path = get_xml()
    command = f'"{SCHTASKS_EXE}" /Create /TN "{TASK_NAME}" /XML "{xml_path.resolve()}" /F'
    run_as_admin(command)

def do_unregister_task():
    """Admin: Deletes the scheduled task."""
    command = f'"{SCHTASKS_EXE}" /Delete /TN "{TASK_NAME}" /F'
    run_as_admin(command)

def do_start_watcher():
    """Admin: Starts the watcher using the launcher script."""
    if generate_watcher_launcher_bat():
        run_as_admin(str(WATCHER_LAUNCHER_BAT))

def do_stop_watcher():
    """Admin: Kills the watcher process by PID."""
    pid_file = get_pid_file()
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text())
            command = f'"{TASKKILL_EXE}" /PID {pid} /F /T'
            run_as_admin(command)
            pid_file.unlink(missing_ok=True)
        except (ValueError, FileNotFoundError):
            pass # PID file was invalid or already gone

# ─── Status Checkers ────────────────────────────────────────────────────────

def is_watcher_online() -> bool:
    pid_file = get_pid_file()
    if not pid_file.exists(): return False
    try:
        return is_pid_alive(int(pid_file.read_text()))
    except (ValueError, FileNotFoundError): return False

def is_task_registered() -> bool:
    try:
        subprocess.check_output([str(SCHTASKS_EXE), '/Query', '/TN', TASK_NAME], stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError: return False

def get_watcher_status() -> str:
    """Returns a user-friendly status string."""
    online = is_watcher_online()
    registered = is_task_registered()
    if online and registered: return f"{Fore.GREEN}Online & Registered{Style.RESET_ALL}"
    if online and not registered: return f"{Fore.GREEN}Online{Style.RESET_ALL} (Not Registered)"
    if not online and registered: return f"{Fore.YELLOW}Offline{Style.RESET_ALL} (Registered)"
    return f"{Fore.RED}Offline & Unregistered{Style.RESET_ALL}"

def wait_for_watcher_online(timeout: int = 15) -> bool:
    """Waits for the watcher PID file to appear and process to be alive."""
    print(Fore.YELLOW + "  -> Waiting for watcher to confirm it is online...", end="", flush=True)
    for _ in range(timeout):
        if is_watcher_online():
            print(Fore.GREEN + " Confirmed!" + Style.RESET_ALL)
            notify_system_event("Watcher Online", "SortedPC is now monitoring files.")
            return True
        time.sleep(1)
    print(Fore.RED + " Timed out. Check 'src/watcher_launch.log' for errors.")
    return False


# ─── Startup Workflow ───────────────────────────────────────────────────────

def startup_check():
    """Main startup routine to ensure the system is ready."""
    print_header("System Startup Check")
    run_initializer()
    print("1. File structure initialized.")

    # 2. Check for organized paths and build FAISS if needed
    organized_paths = get_organized_paths()
    faiss_index_path = get_faiss_index_path()

    if organized_paths and not all(Path(p).exists() for p in organized_paths):
        print(Fore.YELLOW + "Some organized paths no longer exist.")
        if safe_input("Re-build FAISS index from available paths? (y/n): ").lower() == 'y':
            build_from_paths(get_organized_paths())

    # 3. Handle missing FAISS or watch paths
    if not faiss_index_path.exists():
        print(Fore.YELLOW + "FAISS index not found. The system needs an initial set of sorted folders to learn from.")
        if organized_paths:
            if safe_input("Build FAISS index from existing organized paths? (y/n): ").lower() == 'y':
                build_from_paths(organized_paths)
        else:
            print(Fore.RED + "No organized paths are configured. Please add some to build the index.")
            manage_organized_paths_menu()

    if not get_watch_paths():
        print(Fore.YELLOW + "No folders are being watched.")
        manage_watcher_menu()

    # 4. Check watcher status and prompt user
    if not is_watcher_online():
        print(Fore.YELLOW + "\nWatcher is currently offline.")
        if not is_task_registered():
            choice = safe_input("Start the watcher now or register it to run on startup? (start/register/skip): ").lower()
            if choice == 'start':
                do_start_watcher()
                wait_for_watcher_online()
            elif choice == 'register':
                do_register_task()
                print(Fore.GREEN + "Registered to start on next login. You can also start it manually from the menu.")
        else:
            if safe_input("Watcher is registered but offline. Start it now? (y/n): ").lower() == 'y':
                do_start_watcher()
                wait_for_watcher_online()

    print(Fore.GREEN + "\nSystem check complete. Launching main menu.")
    time.sleep(2)


# ─── Sub-Menus ──────────────────────────────────────────────────────────────

def manage_organized_paths_menu():
    """Menu for managing folders the system learns from."""
    while True:
        print_header("Manage Organized Paths")
        paths = get_organized_paths()
        print("Current Organized Paths (used for learning):")
        if paths:
            for i, p in enumerate(paths): print(f"  {i+1}. {p}")
        else:
            print(Fore.YELLOW + "  None configured.")

        print("\n" + "-"*20)
        print("  a. Add a path")
        print("  r. Remove a path")
        print("  b. Re-build FAISS Index Now")
        print("  x. Back to main menu")
        print("-" * 20)
        choice = safe_input("Select: ").lower()

        if choice == 'a':
            new_path = safe_input("Enter the full path to add: ")
            if Path(new_path).is_dir():
                paths.append(new_path)
                with get_paths_file().open("w") as f: json.dump({"watch_paths": get_watch_paths(), "organized_paths": paths}, f, indent=2)
                print(Fore.GREEN + "Path added. Remember to re-build the index.")
            else:
                print(Fore.RED + "Invalid path.")
            time.sleep(1)

        elif choice == 'r':
            try:
                idx = int(safe_input("Enter number of path to remove: ")) - 1
                if 0 <= idx < len(paths):
                    removed = paths.pop(idx)
                    with get_paths_file().open("w") as f: json.dump({"watch_paths": get_watch_paths(), "organized_paths": paths}, f, indent=2)
                    print(Fore.GREEN + f"Removed {removed}. Remember to re-build the index.")
                else:
                    print(Fore.RED + "Invalid number.")
            except ValueError:
                print(Fore.RED + "Invalid input.")
            time.sleep(1)

        elif choice == 'b':
            print("Building FAISS index... this may take a moment.")
            build_from_paths(get_organized_paths())
            print(Fore.GREEN + "Index built successfully.")
            time.sleep(2)

        elif choice == 'x':
            break

def manage_watcher_menu():
    """Menu for managing folders to watch and the watcher process."""
    while True:
        print_header("Manage Watcher")
        print(f"Status: {get_watcher_status()}")
        paths = get_watch_paths()
        print("\nCurrent Watched Paths:")
        if paths:
            for i, p in enumerate(paths): print(f"  {i+1}. {p}")
        else:
            print(Fore.YELLOW + "  None configured.")

        print("\n" + "-"*20)
        print("  a. Add a watch path")
        print("  r. Remove a watch path")
        print("-" * 20)
        print("  s. Start Watcher")
        print("  t. Stop Watcher")
        print("  e. Register for Startup")
        print("  u. Unregister from Startup")
        print("  k. Restart Watcher")
        print("-" * 20)
        print("  x. Back to main menu")
        print("-" * 20)
        choice = safe_input("Select: ").lower()

        if choice == 'a':
            new_path = safe_input("Enter path to watch: ")
            if Path(new_path).is_dir():
                paths.append(new_path)
                with get_paths_file().open("w") as f: json.dump({"watch_paths": paths, "organized_paths": get_organized_paths()}, f, indent=2)
                print(Fore.GREEN + "Path added. Restart watcher to apply changes.")
            else:
                print(Fore.RED + "Invalid path.")
            time.sleep(1)
        elif choice == 'r':
            try:
                idx = int(safe_input("Enter number of path to remove: ")) - 1
                if 0 <= idx < len(paths):
                    paths.pop(idx)
                    with get_paths_file().open("w") as f: json.dump({"watch_paths": paths, "organized_paths": get_organized_paths()}, f, indent=2)
                    print(Fore.GREEN + "Path removed. Restart watcher to apply changes.")
                else:
                    print(Fore.RED + "Invalid number.")
            except ValueError:
                print(Fore.RED + "Invalid input.")
            time.sleep(1)
        elif choice == 's': do_start_watcher(); wait_for_watcher_online()
        elif choice == 't': do_stop_watcher(); time.sleep(1)
        elif choice == 'e': do_register_task(); time.sleep(1)
        elif choice == 'u': do_unregister_task(); time.sleep(1)
        elif choice == 'k':
            do_stop_watcher()
            time.sleep(2)
            do_start_watcher()
            wait_for_watcher_online()
        elif choice == 'x': break

def view_moves_menu():
    """Menu to view and correct past moves."""
    print_header("View & Correct Moves")
    log_file = get_logs_path()
    if not log_file.exists():
        print(Fore.YELLOW + "No moves have been logged yet.")
        time.sleep(2)
        return

    with log_file.open("r") as f:
        logs = [json.loads(line) for line in f if line.strip()]

    moves = [log for log in logs if log.get("category") == "moves"]
    if not moves:
        print(Fore.YELLOW + "No moves have been logged yet.")
        time.sleep(2)
        return

    for i, move in enumerate(reversed(moves[:20])): # Show last 20 moves
        print(f"  {i+1}. {Path(move['file_path']).name} -> {Path(move['final_folder']).name}")

    print("\n" + "-"*20)
    print("  c. Correct a move")
    print("  x. Back to main menu")
    print("-" * 20)
    choice = safe_input("Select: ").lower()

    if choice == 'c':
        try:
            idx = int(safe_input("Enter number of move to correct: ")) - 1
            if 0 <= idx < len(moves):
                move_to_correct = list(reversed(moves[:20]))[idx]
                print(f"Correcting: {Path(move_to_correct['file_path']).name}")
                new_dest = safe_input("Enter the full, correct destination folder path: ")
                if Path(new_dest).is_dir():
                    handle_correction(move_to_correct['file_path'], new_dest)
                    print(Fore.GREEN + "Correction logged and file moved.")
                else:
                    print(Fore.RED + "Invalid destination path.")
            else:
                print(Fore.RED + "Invalid number.")
        except (ValueError, IndexError):
            print(Fore.RED + "Invalid input.")
        time.sleep(2)
    elif choice == 'x':
        return

def learn_menu():
    """Triggers the reinforcement learning process."""
    print_header("Learn from Corrections")
    print("This will analyze past corrections to improve future sorting.")
    if safe_input("Proceed? (y/n): ").lower() == 'y':
        reinforce()
        print(Fore.GREEN + "Learning complete. Weights have been updated.")
    else:
        print(Fore.YELLOW + "Operation cancelled.")
    time.sleep(2)

def reset_all_menu():
    """Resets the entire application to a clean state."""
    print_header("Reset System")
    print(Fore.RED + Style.BRIGHT + "WARNING: This will delete all logs, indexes, and configurations.")
    if safe_input("Are you absolutely sure? Type 'reset' to confirm: ") == 'reset':
        print("Stopping watcher and unregistering...")
        do_stop_watcher()
        time.sleep(1)
        do_unregister_task()
        time.sleep(1)
        print("Deleting data files...")
        data_dir = get_data_dir()
        if data_dir.exists():
            shutil.rmtree(data_dir)
        print(Fore.GREEN + "System has been reset. Please restart the application.")
        sys.exit(0)
    else:
        print(Fore.YELLOW + "Reset cancelled.")
    time.sleep(2)


# ─── Main Application Loop ──────────────────────────────────────────────────

def main_menu():
    """The main menu of the application."""
    while True:
        print_header("SortedPC Main Menu")
        print(f"Watcher Status: {get_watcher_status()}\n")
        print("  1. Manage Organized Paths (Learning Data)")
        print("  2. Manage Watcher")
        print("  3. View & Correct Moves")
        print("  4. Learn from Corrections")
        print("  5. Reset System")
        print("  x. Exit")
        print("-" * 40)
        choice = safe_input("Select: ").lower()

        if choice == '1': manage_organized_paths_menu()
        elif choice == '2': manage_watcher_menu()
        elif choice == '3': view_moves_menu()
        elif choice == '4': learn_menu()
        elif choice == '5': reset_all_menu()
        elif choice == 'x':
            if is_watcher_online():
                print("Stopping watcher...")
                do_stop_watcher()
            print("Goodbye.")
            break

if __name__ == "__main__":
    startup_check()
    main_menu()
