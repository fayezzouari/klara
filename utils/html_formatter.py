import re
import os
from typing import List, Dict, Any

def convert_citations_to_html(text: str, sources_info: List[Dict[str, Any]]) -> str:
    """
    Convert plain text with citations like [p.X] or [p. X] into HTML with clickable links.
    
    Args:
        text: Response text with citations
        sources_info: List of dictionaries with source metadata
        
    Returns:
        HTML formatted text with clickable citation links
    """
    if not sources_info:
        return text
    
    # Create a mapping of titles to file paths
    title_to_info = {src['title']: src for src in sources_info}
    
    # Replace citations with links
    def replace_citation(match):
        page_num = match.group(1).strip()
        
        # If we're in a "Sources:" section, don't convert the text
        text_before = text[:match.start()]
        if "Sources:" in text_before and text_before.rindex("Sources:") > text_before.rfind("\n\n"):
            return match.group(0)
        
        # For citations in the main text, create links to all matching documents at that page
        links = []
        for src in sources_info:
            if src['file_path'] and os.path.exists(src['file_path']):
                title = src['title']
                file_path = src['file_path']
                # Create a link that opens PDF at specific page (works with most PDF viewers)
                link = f'<a href="file://{file_path}#page={page_num}" target="_blank" class="citation-link" title="Open {title} at page {page_num}">{match.group(0)}</a>'
                links.append(link)
        
        if links:
            return links[0]  # Return first link if multiple sources
        else:
            return match.group(0)  # Return original text if no valid sources
    
    # Replace citations in format [p.X] and [p. X]
    html_text = re.sub(r'\[p\.?\s*(\d+)\]', replace_citation, text)
    
    # Add links to source documents at the end
    if "Sources:" in html_text:
        def replace_source(match):
            source_name = match.group(1).strip()
            if source_name in title_to_info and title_to_info[source_name]['file_path']:
                file_path = title_to_info[source_name]['file_path']
                if os.path.exists(file_path):
                    return f'<a href="file://{file_path}" target="_blank" class="source-link" title="Open {source_name}">{source_name}</a>'
            return source_name
        
        # Find the Sources section and add links
        parts = html_text.split("Sources:", 1)
        if len(parts) == 2:
            sources_section = parts[1]
            # Replace each source name with a link
            for source_name in title_to_info.keys():
                sources_section = re.sub(
                    r'\b' + re.escape(source_name) + r'\b',
                    lambda m: replace_source(m), 
                    sources_section
                )
            html_text = parts[0] + "Sources:" + sources_section
    
    # Add some basic styling
    styled_html = f"""
    <div class="qa-response">
      {html_text}
    </div>
    <style>
    .citation-link {{
      color: #007bff;
      text-decoration: none;
      background-color: #f0f7ff;
      padding: 0 3px;
      border-radius: 3px;
      font-weight: bold;
    }}
    .source-link {{
      color: #28a745;
      text-decoration: underline;
      font-weight: bold;
    }}
    .qa-response {{
      line-height: 1.5;
      white-space: pre-wrap;
    }}
    </style>
    """
    
    return styled_html