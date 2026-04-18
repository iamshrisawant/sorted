import sys
import json
import logging
import subprocess
import time
import os
from pathlib import Path
import shutil
import colorama

colorama.init(autoreset=True)
from colorama import Fore, Style

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.pipelines.initializer import run_initializer
from src.core.pipelines.builder import build_from_paths
from src.core.pipelines.actor import handle_correction
from src.core.pipelines.sorter import handle_new_file
from src.core.utils.paths import (
    get_watch_paths, get_organized_paths, get_paths_file,
    get_config_file, get_logs_path, ROOT_DIR,
    get_faiss_index_path, get_data_dir, get_unsorted_folder,
    update_paths, get_folder_contexts, update_folder_contexts
)
from src.core.pipelines.watcher import get_pid_file, is_pid_alive
from src.core.utils.notifier import notify_system_event

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

TASK_NAME = "SortedPC_Watcher"

def safe_input(prompt: str = "") -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print(Fore.YELLOW + "\nExiting.")
        sys.exit(0)

def clear_screen():
    # os.system('cls' if os.name == 'nt' else 'clear')
    pass

def print_header(title: str):
    clear_screen()
    print(Fore.CYAN + "=" * 40)
    print(Style.BRIGHT + f"  {title}".center(40))
    print(Fore.CYAN + "=" * 40 + Style.RESET_ALL)

import platform
import stat

# Removed run_as_admin and old task schedulers. We now rely on user-level native startup hooks avoiding UAC.

def get_watcher_script_path() -> Path:
    return ROOT_DIR / "src" / "core" / "pipelines" / "watcher.py"

def get_pythonw_path() -> str:
    python_dir = Path(sys.executable).parent
    # Check for pythonw.exe on Windows for stealth execution
    if platform.system() == "Windows":
        pythonw_exe = python_dir / "pythonw.exe"
        if pythonw_exe.exists():
            return str(pythonw_exe)
    return sys.executable

def do_start_watcher() -> bool:
    try:
        script = get_watcher_script_path()
        py_exe = get_pythonw_path()
        sys_name = platform.system()
        
        if sys_name == "Windows":
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen([py_exe, str(script)], 
                             creationflags=DETACHED_PROCESS, 
                             cwd=str(ROOT_DIR),
                             close_fds=True)
            return True
        else:
            subprocess.Popen([py_exe, str(script)],
                             start_new_session=True,
                             cwd=str(ROOT_DIR),
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return True
    except Exception as e:
        logger.error(f"Failed to start watcher natively: {e}")
        return False

def do_stop_watcher() -> bool:
    pid_file = get_pid_file()
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text())
            sys_name = platform.system()
            
            if sys_name == "Windows":
                # Fallback to taskkill to violently kill on windows
                subprocess.run(['taskkill', '/PID', str(pid), '/F', '/T'], capture_output=True)
            else:
                import signal
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                    
            # Wait for down
            for _ in range(10):
                if not is_pid_alive(pid):
                    break
                time.sleep(0.5)
            pid_file.unlink(missing_ok=True)
            return True
        except (ValueError, FileNotFoundError):
            pid_file.unlink(missing_ok=True)
            return True
    return True

def get_startup_file_path() -> Path:
    sys_name = platform.system()
    if sys_name == "Windows":
        return Path(os.environ.get("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "SortedPC_Watcher.vbs"
    elif sys_name == "Darwin":
        return Path.home() / "Library" / "LaunchAgents" / "com.sortedpc.watcher.plist"
    else: # Linux
        return Path.home() / ".config" / "systemd" / "user" / "sortedpc.service"

def is_task_registered() -> bool:
    return get_startup_file_path().exists()

def do_register_task():
    try:
        startup_file = get_startup_file_path()
        startup_file.parent.mkdir(parents=True, exist_ok=True)
        py_exe = get_pythonw_path()
        script = get_watcher_script_path()
        sys_name = platform.system()

        if sys_name == "Windows":
            vbs_content = f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run """{py_exe}"" ""{script}""", 0, False'
            startup_file.write_text(vbs_content, encoding="utf-8")
        elif sys_name == "Darwin":
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sortedpc.watcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>{py_exe}</string>
        <string>{script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{ROOT_DIR}</string>
</dict>
</plist>'''
            startup_file.write_text(plist_content, encoding="utf-8")
            subprocess.run(["launchctl", "load", str(startup_file)], capture_output=True)
        else: # Linux
            service_content = f'''[Unit]
Description=SortedPC Background Watcher
After=default.target

[Service]
ExecStart={py_exe} {script}
WorkingDirectory={ROOT_DIR}
Restart=always
RestartSec=3

[Install]
WantedBy=default.target'''
            startup_file.write_text(service_content, encoding="utf-8")
            subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
            subprocess.run(["systemctl", "--user", "enable", "sortedpc.service"], capture_output=True)

        print(Fore.GREEN + "Startup hook registered successfully.")
    except Exception as e:
        print(Fore.RED + f"Failed to register startup hook: {e}")

def do_unregister_task():
    try:
        startup_file = get_startup_file_path()
        sys_name = platform.system()
        
        if sys_name == "Darwin" and startup_file.exists():
            subprocess.run(["launchctl", "unload", str(startup_file)], capture_output=True)
        elif sys_name == "Linux" and startup_file.exists():
            subprocess.run(["systemctl", "--user", "disable", "sortedpc.service"], capture_output=True)
            
        startup_file.unlink(missing_ok=True)
        print(Fore.GREEN + "Startup hook removed successfully.")
    except Exception as e:
        print(Fore.RED + f"Failed to remove startup hook: {e}")

def is_watcher_online() -> bool:
    pid_file = get_pid_file()
    if not pid_file.exists(): return False
    try:
        return is_pid_alive(int(pid_file.read_text()))
    except (ValueError, FileNotFoundError): return False

def get_watcher_status() -> str:
    online = is_watcher_online()
    registered = is_task_registered()
    if online and registered: return f"{Fore.GREEN}Online & Registered{Style.RESET_ALL}"
    if online and not registered: return f"{Fore.GREEN}Online{Style.RESET_ALL} (Not Registered)"
    if not online and registered: return f"{Fore.YELLOW}Offline{Style.RESET_ALL} (Registered)"
    return f"{Fore.RED}Offline & Unregistered{Style.RESET_ALL}"

def wait_for_watcher_online(timeout: int = 60) -> bool:
    print(Fore.YELLOW + "  -> Waiting for watcher to confirm it is online...", end="", flush=True)
    for _ in range(timeout):
        if is_watcher_online():
            print(Fore.GREEN + " Confirmed!" + Style.RESET_ALL)
            return True
        time.sleep(1)
    print(Fore.RED + " Timed out. Check 'src/watcher_launch.log' for errors.")
    return False

def startup_check(interactive: bool = True):
    """Main startup routine to ensure the system is ready."""
    print_header("System Startup Check")
    run_initializer()
    print("1. File structure initialized.")

    if not interactive:
        # For UI launches, we stop here and let the UI handle empty states
        return

    organized_paths = get_organized_paths()
    faiss_index_path = get_faiss_index_path()

    if organized_paths and not all(Path(p).exists() for p in organized_paths):
        print(Fore.YELLOW + "Some sorting destinations no longer exist.")
        if safe_input("Update sorting rules to remove them? (y/n): ").lower() == 'y':
            build_from_paths(get_organized_paths())

    if not faiss_index_path.exists():
        print(Fore.YELLOW + "System AI has no active rules. It needs initial sorting destinations to learn from.")
        if organized_paths:
            if safe_input("Activate existing sorting destinations? (y/n): ").lower() == 'y':
                build_from_paths(organized_paths)
        else:
            print(Fore.RED + "No sorting destinations are configured. Please add some first.")
            manage_destinations_menu()

    if not get_watch_paths():
        print(Fore.YELLOW + "No folders are being watched.")
        manage_watcher_menu()

    if not is_watcher_online():
        print(Fore.YELLOW + "\nWatcher is currently offline.")
        if not is_task_registered():
            choice = safe_input("Start the watcher now or register it to run on startup? (start/register/skip): ").lower()
            if choice == 'start':
                if do_start_watcher():
                    wait_for_watcher_online()
            elif choice == 'register':
                do_register_task()
                print(Fore.GREEN + "Registered to start on next login. You can also start it manually from the menu.")
        else:
            if safe_input("Watcher is registered but offline. Start it now? (y/n): ").lower() == 'y':
                if do_start_watcher():
                    wait_for_watcher_online()

    print(Fore.GREEN + "\nSystem check complete. Launching main menu.")
    time.sleep(2)

def manage_destinations_menu():
    while True:
        print_header("Manage Sorting Destinations")
        paths = get_organized_paths()
        contexts = get_folder_contexts()
        
        print("Current Sorting Destinations:")
        if paths:
            for i, p in enumerate(paths):
                print(f"  {i+1}. {p}")
                if p in contexts:
                    text = contexts[p]
                    print(Fore.CYAN + f"     Rule: \"{text[:60]}{'...' if len(text)>60 else ''}\"")
        else:
            print(Fore.YELLOW + "  None configured.")

        print("\n" + "-"*20)
        print("  a. Add a destination folder")
        print("  r. Remove a destination folder")
        print("  s. Save & Update Sorting Rules")
        print("  x. Back to main menu")
        print("-" * 20)
        choice = safe_input("Select: ").lower()

        if choice == 'a':
            new_path_str = safe_input("Enter the full explicit folder path:\n> ")
            new_path = Path(new_path_str).resolve()
            
            if not new_path.exists():
                print(Fore.YELLOW + f"The folder '{new_path.name}' does not exist.")
                create_it = safe_input("Would you like to create it now? (y/n): ").lower()
                if create_it == 'y':
                    try:
                        new_path.mkdir(parents=True, exist_ok=True)
                        print(Fore.GREEN + f"Created folder: {new_path}")
                    except Exception as e:
                        print(Fore.RED + f"Failed to create folder: {e}")
                        time.sleep(2)
                        continue
                else:
                    print(Fore.RED + "Operation cancelled.")
                    time.sleep(1)
                    continue

            p_str = str(new_path)
            if not any(Path(p) in new_path.parents or p == p_str for p in paths):
                paths.append(p_str)
                update_paths({"organized_paths": paths})
                print(Fore.GREEN + "Folder registered as a sorting destination.")
            else:
                print(Fore.YELLOW + "This folder (or its parent) is already registered.")
            
            text = safe_input("Optional: What kind of files should go here? (Enter description, or leave blank to skip):\n> ")
            if text.strip():
                contexts[p_str] = text.strip()
                update_folder_contexts(contexts)
                print(Fore.GREEN + "Sorting rules saved.")
                
            print(Fore.CYAN + "Updating rules so changes apply immediately... Please wait.")
            build_from_paths(get_organized_paths())
            print(Fore.GREEN + "Done!")
            time.sleep(2)

        elif choice == 'r':
            try:
                idx = int(safe_input("Enter number of destination to remove: ")) - 1
                if 0 <= idx < len(paths):
                    removed = paths.pop(idx)
                    update_paths({"organized_paths": paths})
                    if removed in contexts:
                        del contexts[removed]
                        update_folder_contexts(contexts)
                    print(Fore.GREEN + f"Removed {removed}. Updating rules... Please wait.")
                    build_from_paths(get_organized_paths())
                    print(Fore.GREEN + "Done!")
                else:
                    print(Fore.RED + "Invalid number.")
            except ValueError:
                print(Fore.RED + "Invalid input.")
            time.sleep(1)

        elif choice == 's':
            print("Applying new rules... Please wait.")
            build_from_paths(get_organized_paths())
            print(Fore.GREEN + "Rules updated successfully.")
            time.sleep(2)

        elif choice == 'x':
            break

def manage_watcher_menu():
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
                update_paths({"watch_paths": paths})
                print(Fore.GREEN + "Path added. Restart watcher to apply changes.")
            else:
                print(Fore.RED + "Invalid path.")
            time.sleep(1)
        elif choice == 'r':
            try:
                idx = int(safe_input("Enter number of path to remove: ")) - 1
                if 0 <= idx < len(paths):
                    paths.pop(idx)
                    update_paths({"watch_paths": paths})
                    print(Fore.GREEN + "Path removed. Restart watcher to apply changes.")
                else:
                    print(Fore.RED + "Invalid number.")
            except ValueError:
                print(Fore.RED + "Invalid input.")
            time.sleep(1)
        elif choice == 's': 
            if do_start_watcher(): wait_for_watcher_online()
        elif choice == 't': do_stop_watcher(); time.sleep(1)
        elif choice == 'e': do_register_task(); time.sleep(1)
        elif choice == 'u': do_unregister_task(); time.sleep(1)
        elif choice == 'k':
            if do_stop_watcher():
                time.sleep(1)
                if do_start_watcher():
                    wait_for_watcher_online()
        elif choice == 'x': break

def review_history_menu():
    while True:
        print_header("Review Sorting History & Fix Mistakes")
        log_file = get_logs_path()
        if not log_file.exists():
            print(Fore.YELLOW + "No history found.")
            time.sleep(2)
            return

        with log_file.open("r") as f:
            logs = [json.loads(line) for line in f if line.strip()]

        moves = [log for log in logs if log.get("category") == "moves"]
        if not moves:
            print(Fore.YELLOW + "No history has been logged yet.")
            time.sleep(2)
            return

        for i, move in enumerate(reversed(moves[-20:])):
            print(f"  {i+1}. {Path(move['file_path']).name} -> {Path(move['final_folder']).name}")

        print("\n" + "-"*20)
        print("  c. Fix a mistake")
        print("  x. Back to main menu")
        print("-" * 20)
        choice = safe_input("Select: ").lower()

        if choice == 'c':
            try:
                idx = int(safe_input("Enter number of move to fix: ")) - 1
                if 0 <= idx < len(moves):
                    move_to_correct = list(reversed(moves[-20:]))[idx]
                    print(f"Correcting: {Path(move_to_correct['file_path']).name}")
                    new_dest = safe_input("Enter the full, correct destination folder path: ")
                    
                    if Path(new_dest).is_dir():
                        handle_correction(move_to_correct['file_path'], new_dest)
                        print(Fore.GREEN + "Mistake fixed. Updating knowledge engine...")
                        
                        from src.core.utils.paths import get_organized_paths, update_paths, normalize_path
                        from src.core.pipelines.builder import build_from_paths
                        import threading
                        
                        norm_dest = normalize_path(new_dest)
                        organized = get_organized_paths()
                        
                        is_covered = False
                        for p in organized:
                            try:
                                if Path(norm_dest).is_relative_to(Path(p)):
                                    is_covered = True
                                    break
                            except AttributeError: # Fallback for extremely old Pythons
                                if norm_dest.startswith(p):
                                    is_covered = True
                                    break
                                    
                        if not is_covered:
                            print(Fore.YELLOW + f"New destination detected. Learning folder: {Path(norm_dest).name}")
                            organized.append(norm_dest)
                            update_paths({"organized_paths": organized})
                            threading.Thread(target=build_from_paths, args=([norm_dest],), daemon=True).start()
                            notify_system_event("Learning Complete", "AI has indexed a newly corrected folder destination.")
                        else:
                            notify_system_event("Correction Logged", "Mistake fixed into an existing knowledge folder.")
                            
                        print(Fore.GREEN + "Correction successfully processed!")
                    else:
                        print(Fore.RED + "Invalid destination path.")
                else:
                    print(Fore.RED + "Invalid number.")
            except (ValueError, IndexError):
                print(Fore.RED + "Invalid input.")
            time.sleep(2)
        elif choice == 'x':
            break

def manual_sort_menu():
    print_header("Manual Sort Folder")
    print("This will sort all existing files in a directory.")
    print(f"Default unsorted folder: {get_unsorted_folder()}")
    
    path_str = safe_input("Enter folder path to sort (leave blank for default): ").strip()
    if not path_str:
        folder = get_unsorted_folder()
    else:
        folder = Path(path_str)

    if not folder.exists() or not folder.is_dir():
        print(Fore.RED + "Invalid directory.")
        time.sleep(2)
        return

    print(Fore.YELLOW + f"Scanning {folder}...")
    
    # Use iterative approach to avoid recursion depth issues as requested
    files_to_process = []
    stack = [folder]
    while stack:
        curr = stack.pop()
        try:
            for item in curr.iterdir():
                if item.is_file():
                    # Basic filters matching builder/watcher logic
                    if not item.name.startswith(("~", ".")):
                        files_to_process.append(item)
                elif item.is_dir():
                    stack.append(item)
        except PermissionError:
            continue

    if not files_to_process:
        print(Fore.YELLOW + "No files found to sort.")
        time.sleep(2)
        return

    print(Fore.CYAN + f"Found {len(files_to_process)} files. Starting sort...")
    
    success_count = 0
    for i, file_path in enumerate(files_to_process):
        print(f"[{i+1}/{len(files_to_process)}] Sorting: {file_path.name}")
        try:
            handle_new_file(str(file_path))
            success_count += 1
        except Exception as e:
            print(Fore.RED + f"Error sorting {file_path.name}: {e}")

    print(Fore.GREEN + f"\nManual sort complete. Successfully processed {success_count}/{len(files_to_process)} files.")
    notify_system_event("Manual Sort", f"Successfully processed {success_count} files in {folder.name}.")
    time.sleep(3)

def reset_all_menu():
    print_header("Reset System")
    print(Fore.RED + Style.BRIGHT + "WARNING: This will delete all logs, indexes, and configurations.")
    if safe_input("Are you absolutely sure? Type 'reset' to confirm: ") == 'reset':
        print("Stopping watcher and unregistering...")
        from src.core.utils.paths import update_config
        update_config({"system_resetting": True})
        
        if not do_stop_watcher():
            print(Fore.RED + "Cannot safely reset system while the watcher is still locked. Aborting.")
            update_config({"system_resetting": False})
            time.sleep(2)
            return
            
        # Extra sleep to guarantee the OS has released all file locks
        time.sleep(1) 
        do_unregister_task()
        time.sleep(1)
        
        print("Deleting data files...")
        data_dir = get_data_dir()
        if data_dir.exists():
            shutil.rmtree(data_dir, ignore_errors=True)
        
        # Re-initialize will clear the flag if it creates a new config
        print(Fore.GREEN + "System has been reset. Please restart the application.")
        sys.exit(0)
    else:
        print(Fore.YELLOW + "Reset cancelled.")
    time.sleep(2)

def main_menu():
    while True:
        print_header("SortedPC Main Menu")
        print(f"Watcher Status: {get_watcher_status()}\n")
        print("  1. Manage Sorting Destinations (Folders & Rules)")
        print("  2. Manage Background Watcher")
        print("  3. Review Sorting History & Fix Mistakes")
        print("  4. Sort Inbox Now")
        print("  5. Reset System")
        print("  x. Exit")
        print("-" * 40)
        choice = safe_input("Select: ").lower()

        if choice == '1': manage_destinations_menu()
        elif choice == '2': manage_watcher_menu()
        elif choice == '3': review_history_menu()
        elif choice == '4': manual_sort_menu()
        elif choice == '5': reset_all_menu()
        elif choice == 'x':
            print("Goodbye.")
            break

import argparse

def launch_ui():
    print(Fore.CYAN + "Starting Desktop UI..." + Style.RESET_ALL)
    # We will import the desktop launcher here to avoid circular imports / missing deps
    try:
        from src.api.desktop import run_desktop_app
        run_desktop_app()
    except ImportError as e:
        print(Fore.RED + f"Failed to load UI components: {e}")
        print(Fore.YELLOW + "Falling back to CLI...")
        main_menu()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SortedPC Semantic Watcher")
    parser.add_argument("--cli", action="store_true", help="Launch the terminal CLI instead of the Desktop UI")
    args = parser.parse_args()

    # Always initialize models/folders first
    startup_check(interactive=args.cli)

    if args.cli:
        main_menu()
    else:
        launch_ui()