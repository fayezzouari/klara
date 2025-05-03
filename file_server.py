"""
Simple HTTP server to serve document files for viewing.
Run this in a separate terminal to make document links work.
"""
import os
import http.server
import socketserver
from typing import Optional
import threading
import webbrowser

# Configure the file serving directory
FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")
os.makedirs(FILE_DIR, exist_ok=True)

PORT = 8089  # Use a port unlikely to conflict with other services

class FileServerHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that serves from the file directory regardless of current working dir"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FILE_DIR, **kwargs)
    
    def log_message(self, format, *args):
        # Quieter logging
        if len(args) >= 3 and (args[1] == '200' or args[1] == '304'):
            return  # Don't log successful requests
        super().log_message(format, *args)

def run_server():
    """Start the file server"""
    with socketserver.TCPServer(("", PORT), FileServerHandler) as httpd:
        print(f"File server started at http://localhost:{PORT}")
        print(f"Serving files from: {FILE_DIR}")
        httpd.serve_forever()

def start_server():
    """Start the server in a background thread"""
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True  # Thread will close when main program exits
    server_thread.start()
    return server_thread

def get_file_url(filename: str) -> str:
    """Get URL for a file in the server"""
    return f"http://localhost:{PORT}/{filename}"

if __name__ == "__main__":
    run_server()  # If run directly, start the server in the foreground