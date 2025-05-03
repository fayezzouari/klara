"""
File service utilities for handling document storage and serving.
"""
import os
import shutil
import tempfile
from typing import Optional, Tuple

# Use the file server's directory
from file_server import FILE_DIR, get_file_url

# Use the file server's directory for serving
SERVE_DIR = FILE_DIR

def copy_to_serve_dir(file_path: str, filename: str = None) -> str:
    """Copy a file to the serve directory for web access.
    
    Args:
        file_path: Source file path
        filename: Optional filename to use (if None, uses the basename of file_path)
        
    Returns:
        str: Web-accessible path to the served file
    """
    if not os.path.exists(file_path):
        return None
        
    if filename is None:
        filename = os.path.basename(file_path)
    
    # Clean the filename - replace spaces with underscores to avoid URL encoding issues
    clean_filename = filename.replace(' ', '_')
    
    # Ensure filename is unique
    base_name, ext = os.path.splitext(clean_filename)
    counter = 1
    dest_filename = clean_filename
    
    while os.path.exists(os.path.join(SERVE_DIR, dest_filename)):
        dest_filename = f"{base_name}_{counter}{ext}"
        counter += 1
    
    # Copy the file to the serve directory
    dest_path = os.path.join(SERVE_DIR, dest_filename)
    shutil.copy2(file_path, dest_path)
    
    # Make sure the destination file exists
    if os.path.exists(dest_path):
        print(f"File copied successfully: {dest_path}")
    else:
        print(f"Failed to copy file to {dest_path}")
    
    # Return a web-accessible URL using our file server
    url = get_file_url(dest_filename)
    print(f"File URL: {url}")
    return url

def save_temp_file(file_obj) -> Optional[Tuple[str, str]]:
    """Save an uploaded file to a temporary location.
    
    Args:
        file_obj: File object to save (can be various formats)
        
    Returns:
        Tuple[str, str]: Tuple of (file_path, filename) or (None, None) on failure
    """
    try:
        # Handle Gradio file object
        if isinstance(file_obj, tuple) and len(file_obj) == 2:
            file_path = file_obj[1]
            # If the file already exists on disk, return its path
            if os.path.exists(file_path):
                return file_path, os.path.basename(file_path)
        
        # Get original filename if available
        original_filename = None
        if hasattr(file_obj, 'name'):
            original_filename = os.path.basename(file_obj.name)
            
        # Determine file extension
        file_ext = '.tmp'
        if original_filename:
            _, file_ext = os.path.splitext(original_filename)
        
        # Create a temporary file with the appropriate extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            if hasattr(file_obj, 'read'):
                # If it's a file-like object with read method
                tmp.write(file_obj.read())
            elif isinstance(file_obj, bytes):
                # If it's raw bytes
                tmp.write(file_obj)
            elif isinstance(file_obj, str):
                # If it's a file path
                if os.path.exists(file_obj):
                    with open(file_obj, 'rb') as f:
                        tmp.write(f.read())
                else:
                    # If it's a string content
                    tmp.write(file_obj.encode())
            else:
                # For Gradio newer versions, the file is directly provided as a path
                return file_obj, original_filename or os.path.basename(file_obj)
                
            return tmp.name, original_filename or os.path.basename(tmp.name)
    except Exception as e:
        print(f"Error saving temporary file: {e}")
        return None, None