"""
Utility functions for formatting markdown outputs from raw text responses.
"""
import re
import os
from typing import Dict, List, Any

def convert_citations_to_markdown(text: str, sources_info: List[Dict[str, Any]]) -> str:
    """
    Convert citations in the form [N-P] to clickable markdown links.
    
    Args:
        text (str): The text response with citations
        sources_info (List[Dict]): List of source information with file_path and source_num
        
    Returns:
        str: Markdown text with clickable citations
    """
    if not sources_info:
        return text
    
    # Create a mapping of source numbers to file paths
    source_map = {}
    for src in sources_info:
        if "source_num" in src and "file_path" in src:
            # Store the complete URL as provided by the file server
            source_map[src["source_num"]] = src["file_path"]
    
    # Replace citations with markdown links
    def replace_citation(match):
        citation = match.group(0)  # The full citation, e.g., [1-3]
        
        # Extract the source number and page number
        match_parts = re.match(r'\[(\d+)-(\d+)\]', citation)
        if not match_parts:
            return citation
            
        source_num = int(match_parts.group(1))
        page_num = int(match_parts.group(2))
        
        # If we have a file path for this source, create a link
        if source_num in source_map and source_map[source_num]:
            # Use the URL directly as provided by file_service
            url = source_map[source_num]
            # Add page anchor for PDF.js viewer - #page=N format
            if url.endswith('.pdf') or '.pdf' in url:
                url = f"{url}#page={page_num}"
            return f"[{citation}]({url})"
        
        return citation
    
    # Find and replace all citations in the format [N-P]
    processed_text = re.sub(r'\[\d+-\d+\]', replace_citation, text)
    
    # Also make the sources section entries clickable
    lines = processed_text.split('\n')
    sources_section_started = False
    
    for i, line in enumerate(lines):
        if line.strip() == "Sources:" or line.strip() == "Sources:":
            sources_section_started = True
            continue
            
        if sources_section_started:
            # Match lines like "[1] Document Title"
            match = re.match(r'^\[(\d+)\]\s+(.+)$', line.strip())
            if match:
                source_num = int(match.group(1))
                
                if source_num in source_map and source_map[source_num]:
                    url = source_map[source_num]
                    lines[i] = f"[{line.strip()}]({url})"
    
    # Convert back to text
    return "\n".join(lines)