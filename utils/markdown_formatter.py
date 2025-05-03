import re
import os
from typing import List, Dict, Any
import urllib.parse

def convert_citations_to_markdown(text: str, sources_info: List[Dict[str, Any]]) -> str:
    """
    Convert plain text with citations like [N-P] into HTML with clickable links.
    
    Args:
        text: Response text with citations in [N-P] format
        sources_info: List of dictionaries with source metadata
        
    Returns:
        HTML formatted text with clickable citation links
    """
    if not sources_info:
        return text
    
    # Create a mapping of source numbers to file paths and titles
    source_num_to_info = {src['source_num']: src for src in sources_info}
    
    # Replace citations with links
    def replace_citation(match):
        source_num = int(match.group(1))
        page_num = int(match.group(2))
        citation_text = match.group(0)
        
        # If we're in a "Sources:" section, don't convert the text
        text_before = text[:match.start()]
        if "Sources:" in text_before and text_before.rindex("Sources:") > text_before.rfind("\n\n"):
            return citation_text
        
        # Check if we have info for this source number
        if source_num in source_num_to_info:
            src = source_num_to_info[source_num]
            if src['file_path'] and os.path.exists(src['file_path']):
                title = src['title']
                # Use absolute file path with proper URL encoding
                file_path = "file://" + urllib.parse.quote(os.path.abspath(src['file_path']))
                
                # Create HTML link directly
                return f'<a href="{file_path}#page={page_num}" target="_blank" title="{title}, page {page_num}" style="color: #2C7BE5; text-decoration: underline;">{citation_text}</a>'
        
        return citation_text  # Return original text if no valid sources
    
    # Replace citations in format [N-P]
    html_text = re.sub(r'\[(\d+)-(\d+)\]', replace_citation, text)
    
    # Add links to source documents in the Sources section
    if "Sources:" in html_text:
        # Process each source reference like [1] Document Title
        def replace_source_ref(match):
            source_num = int(match.group(1))
            if source_num in source_num_to_info:
                src = source_num_to_info[source_num]
                if src['file_path'] and os.path.exists(src['file_path']):
                    file_path = "file://" + urllib.parse.quote(os.path.abspath(src['file_path']))
                    return f'<a href="{file_path}" target="_blank" title="Open {src["title"]}" style="color: #28a745; font-weight: bold;">[{source_num}]</a>'
            return match.group(0)
        
        html_text = re.sub(r'\[(\d+)\](?=\s+\w+)', replace_source_ref, html_text)
    
    # Wrap in a div for styling and preserve line breaks with <br> tags
    styled_html = html_text.replace("\n\n", "<br><br>").replace("\n", "<br>")
    
    # Add final wrapper
    final_html = f"""<div style="line-height: 1.5;">{styled_html}</div>"""
    
    return final_html