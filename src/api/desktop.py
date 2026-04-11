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

class DesktopAPI:
    def pick_folder(self):
        try:
            window = webview.windows[0]
            result = window.create_file_dialog(webview.FileDialog.FOLDER)
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            print(f"Error opening folder picker: {e}")
            return None

def run_desktop_app():
    # Start FastAPI in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait briefly for server to boot
    import time
    time.sleep(1)

    # Resolve UI paths
    ui_path = Path(PROJECT_ROOT) / "ui" / "index.html"
    
    if not ui_path.exists():
        print(f"Error: Could not find UI at {ui_path}")
        return

    # Create the window
    api = DesktopAPI()
    window = webview.create_window(
        title="SortedPC",
        url=f"file://{ui_path.resolve()}",
        js_api=api,
        width=1100,
        height=750,
        min_size=(900, 600),
        frameless=False,
        easy_drag=True,
        background_color='#0B0F19'
    )
    webview.start(debug=False)

if __name__ == "__main__":
    run_desktop_app()
