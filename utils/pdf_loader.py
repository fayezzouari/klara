"""
Enhanced PDF loader that can handle PDF forms with buttons and other problematic elements.
"""
import os
import tempfile
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from langchain_core.documents import Document

class RobustPDFLoader:
    """PDF Loader that handles problematic PDFs with form elements.
    
    Uses PyMuPDF (fitz) instead of PyPDF2 for more robust parsing.
    """
    
    def __init__(self, file_path: str):
        """Initialize with the path to the PDF file."""
        self.file_path = file_path
        
    def load(self) -> List[Document]:
        """Load the PDF and return a list of Document objects."""
        try:
            documents = []
            # Open the PDF with PyMuPDF
            with fitz.open(self.file_path) as pdf:
                # Extract text from each page
                for page_num, page in enumerate(pdf):
                    text = page.get_text()
                    # Create Document object
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": self.file_path,
                            "page": page_num,
                            "total_pages": len(pdf)
                        }
                    )
                    documents.append(doc)
                    
            return documents
            
        except Exception as e:
            print(f"Error loading PDF with RobustPDFLoader: {e}")
            # Try alternative methods or return empty list
            return []
            
    @classmethod
    def from_path(cls, file_path: str) -> "RobustPDFLoader":
        """Create a loader instance from a file path."""
        return cls(file_path)