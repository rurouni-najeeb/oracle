import threading
import uvicorn
import webview
from app.main import app

PORT = 8787


def start_server():
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    webview.create_window("Oracle", f"http://127.0.0.1:{PORT}", width=1400, height=900)
    webview.start()
