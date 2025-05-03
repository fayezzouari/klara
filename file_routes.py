"""
Defines file serving routes for Gradio to access document files.
This makes PDFs accessible for viewing when clicked in the interface.
"""
import os
import gradio as gr

# Define the files directory
FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")

# Make sure the directory exists
os.makedirs(FILES_DIR, exist_ok=True)

def setup_file_routes(app):
    """
    Add file serving routes to the Gradio app.
    
    Args:
        app: The FastAPI app used by Gradio
    """
    @app.get("/files/{file_path:path}")
    async def serve_file(file_path: str):
        """Serve files from the files directory."""
        file_full_path = os.path.join(FILES_DIR, file_path)
        return gr.File(file_full_path)