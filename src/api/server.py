import os
import time
import json
import shutil
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

# Safe imports from core
from src.core.utils.paths import (
    get_organized_paths, get_folder_contexts, update_paths, 
    update_folder_contexts, get_watch_paths, get_logs_path, get_unsorted_folder, get_data_dir
)
from src.core.pipelines.builder import build_from_paths
from src.core.pipelines.actor import handle_correction
from src.core.pipelines.sorter import handle_new_file

# Import OS level manager functions from main securely
from src.main import (
    is_watcher_online, is_task_registered, do_start_watcher, 
    do_stop_watcher, do_register_task, do_unregister_task
)

app = FastAPI(title="SortedPC Headless Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Destination(BaseModel):
    path: str
    context: str

class Correction(BaseModel):
    original_file: str
    new_folder: str

class PathModel(BaseModel):
    path: str

class SortManualInput(BaseModel):
    target_folder: Optional[str] = None

@app.get("/api/status")
def get_status():
    return {
        "online": is_watcher_online(),
        "registered": is_task_registered(),
        "watch_paths": get_watch_paths(),
        "total_destinations": len(get_organized_paths())
    }

@app.post("/api/watcher/control")
def control_watcher(action: str):
    if action == "start":
        res = do_start_watcher()
    elif action == "stop":
        res = do_stop_watcher()
    elif action == "register":
        do_register_task()
        res = True
    elif action == "unregister":
        do_unregister_task()
        res = True
    elif action == "restart":
        if do_stop_watcher():
            time.sleep(1)
            res = do_start_watcher()
        else:
            res = False
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    return {"success": res}

@app.get("/api/watcher/paths")
def get_watcher_paths():
    return get_watch_paths()

@app.post("/api/watcher/paths")
def add_watcher_path(path_in: PathModel):
    paths = get_watch_paths()
    new_path = str(Path(path_in.path).resolve())
    if Path(new_path).is_dir():
        if new_path not in paths:
            paths.append(new_path)
            update_paths({"watch_paths": paths})
        return {"success": True}
    raise HTTPException(status_code=400, detail="Invalid directory path.")

@app.delete("/api/watcher/paths")
def remove_watcher_path(path: str):
    paths = get_watch_paths()
    if path in paths:
        paths.remove(path)
        update_paths({"watch_paths": paths})
    return {"success": True}

@app.get("/api/knowledge/destinations")
def get_destinations():
    paths = get_organized_paths()
    contexts = get_folder_contexts()
    return [{"path": p, "context": contexts.get(p, "")} for p in paths]

@app.post("/api/knowledge/destinations")
def add_destination(dest: Destination, background_tasks: BackgroundTasks):
    paths = get_organized_paths()
    contexts = get_folder_contexts()
    
    p_str = str(Path(dest.path).resolve())
    if not Path(p_str).exists():
        try:
            Path(p_str).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    if not any(Path(p) in Path(p_str).parents or p == p_str for p in paths):
        paths.append(p_str)
        update_paths({"organized_paths": paths})
    
    if dest.context.strip():
        contexts[p_str] = dest.context.strip()
        update_folder_contexts(contexts)
        
    def bg_rebuild():
        try:
            build_from_paths(get_organized_paths())
        except Exception as e:
            print(f"Error rebuilding: {e}")
            
    background_tasks.add_task(bg_rebuild)
    return {"success": True, "message": "Destination added and indexing started."}

@app.delete("/api/knowledge/destinations")
def remove_destination(path: str, background_tasks: BackgroundTasks):
    paths = get_organized_paths()
    contexts = get_folder_contexts()
    
    if path in paths:
        paths.remove(path)
        update_paths({"organized_paths": paths})
    if path in contexts:
        del contexts[path]
        update_folder_contexts(contexts)
        
    def bg_rebuild():
        build_from_paths(get_organized_paths())
        
    background_tasks.add_task(bg_rebuild)
    return {"success": True}

@app.get("/api/history")
def get_history():
    log_file = get_logs_path()
    if not log_file.exists():
        return []
    try:
        with log_file.open("r") as f:
            logs = [json.loads(line) for line in f if line.strip()]
        moves = [log for log in logs if log.get("category") == "moves"]
        return list(reversed(moves[-50:]))
    except Exception as e:
        return []

@app.post("/api/history/correct")
def correct_history(corr: Correction, background_tasks: BackgroundTasks):
    if not Path(corr.new_folder).is_dir():
        raise HTTPException(status_code=400, detail="Invalid destination path")
        
    try:
        handle_correction(corr.original_file, corr.new_folder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    def check_and_learn():
        from src.core.utils.paths import normalize_path
        from src.core.utils.notifier import notify_system_event
        norm_dest = normalize_path(corr.new_folder)
        organized = get_organized_paths()
        is_covered = False
        for p in organized:
            try:
                if Path(norm_dest).is_relative_to(Path(p)):
                    is_covered = True
                    break
            except AttributeError:
                if norm_dest.startswith(p):
                    is_covered = True
                    break
                    
        if not is_covered:
            organized.append(norm_dest)
            update_paths({"organized_paths": organized})
            build_from_paths([norm_dest])
            notify_system_event("Learning Complete", "AI has indexed a newly corrected folder destination.")
            
    background_tasks.add_task(check_and_learn)
    return {"success": True}

@app.post("/api/sort/manual")
def sort_inbox(params: SortManualInput, background_tasks: BackgroundTasks):
    def run_sort():
        # Default fallback or explicit path
        folder = Path(params.target_folder) if params.target_folder else get_unsorted_folder()
        if not folder.exists() or not folder.is_dir():
            return
            
        files_to_process = []
        stack = [folder]
        while stack:
            curr = stack.pop()
            try:
                for item in curr.iterdir():
                    if item.is_file() and not item.name.startswith(("~", ".")):
                        files_to_process.append(item)
                    elif item.is_dir():
                        stack.append(item)
            except PermissionError:
                continue
        for file_path in files_to_process:
            try:
                handle_new_file(str(file_path))
            except Exception:
                pass
    background_tasks.add_task(run_sort)
    return {"success": True, "message": "Manual sorting started in background."}

@app.post("/api/system/reset")
def reset_system():
    if not do_stop_watcher():
        raise HTTPException(status_code=400, detail="Failed to stop watcher. Cannot reset.")
    time.sleep(1)
    do_unregister_task()
    
    data_dir = get_data_dir()
    if data_dir.exists():
        shutil.rmtree(data_dir, ignore_errors=True)
        
    from src.core.pipelines.initializer import run_initializer
    # The old main menu does sys.exit(0) but here we can just reset and return
    import threading
    threading.Thread(target=lambda: run_initializer(force_reset=True)).start()
    return {"success": True}
