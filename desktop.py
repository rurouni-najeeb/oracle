import os
import sys
import threading
import uvicorn
import webview

PORT = 8787


def _get_bundle_dir() -> str:
    if getattr(sys, "_MEIPASS", None):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def start_server():
    os.chdir(_get_bundle_dir())
    from app.main import app

    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    webview.create_window("Oracle", f"http://127.0.0.1:{PORT}", width=1400, height=900)
    webview.start()
