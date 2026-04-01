import os
import sys
import threading
import uvicorn
import webview
from pathlib import Path

# Fix path to load correct module
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_server():
    from src.api.server import app
    uvicorn.run(app, host="127.0.0.1", port=8099, log_level="error")

def run_desktop_app():
    # Start FastAPI in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait briefly for server to boot
    import time
    time.sleep(1)

    # Resolve UI paths
    ui_path = Path(PROJECT_ROOT) / "ui" / "index.html"
    icon_path = Path(PROJECT_ROOT) / "assets" / "icon.ico"
    
    if not ui_path.exists():
        print(f"Error: Could not find UI at {ui_path}")
        return

    icon_arg = str(icon_path.resolve()) if icon_path.exists() else None

    # Create the window
    window = webview.create_window(
        title="SortedPC",
        url=f"file://{ui_path.resolve()}",
        width=1100,
        height=750,
        frameless=False,
        easy_drag=True,
        background_color='#0B0F19'
    )
    webview.start(debug=False, icon=icon_arg)

if __name__ == "__main__":
    run_desktop_app()
