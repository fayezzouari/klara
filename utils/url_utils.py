import os
import tempfile
import requests
from urllib.parse import urlparse
import re
import time
from typing import Tuple, List, Optional

def is_valid_url(url: str) -> bool:
    """Check if a URL is valid.
    
    Args:
        url: URL to check
        
    Returns:
        Boolean indicating if the URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def is_pdf_url(url: str) -> bool:
    """Check if a URL points to a PDF file.
    
    Args:
        url: URL to check
        
    Returns:
        Boolean indicating if the URL points to a PDF
    """
    # Check URL path ends with .pdf
    if url.lower().endswith('.pdf'):
        return True
        
    # Check content type
    try:
        response = requests.head(url, timeout=5)
        content_type = response.headers.get('Content-Type', '')
        return 'application/pdf' in content_type.lower()
    except Exception:
        return False

def download_pdf(url: str, max_retries: int = 3) -> Tuple[Optional[str], Optional[str]]:
    """Download a PDF from a URL and save it to a temporary file.
    
    Args:
        url: URL to download from
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (file_path, filename) or (None, None) if download fails
    """
    if not is_valid_url(url):
        print(f"Invalid URL: {url}")
        return None, None
        
    # Common browser headers to avoid 403 errors
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml,application/pdf;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    # Try different approaches with retries
    for attempt in range(max_retries):
        try:
            print(f"Download attempt {attempt + 1}/{max_retries} for {url}")
            
            # Try with standard GET request first
            if attempt == 0:
                response = requests.get(url, headers=headers, stream=True, timeout=30)
            # Then try with session and referrer
            elif attempt == 1:
                session = requests.Session()
                session.headers.update(headers)
                # Add referrer (usually helps bypass some restrictions)
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                session.headers.update({'Referer': base_url})
                response = session.get(url, stream=True, timeout=30)
            # Last attempt with additional cookies consent header
            else:
                session = requests.Session()
                session.headers.update(headers)
                session.headers.update({
                    'Cookie': 'cookieconsent=true; visited=true',
                    'DNT': '1'
                })
                response = session.get(url, stream=True, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Verify it's a PDF (either by Content-Type or URL)
                is_pdf = 'application/pdf' in content_type or url.lower().endswith('.pdf')
                if not is_pdf:
                    print(f"Warning: Downloaded content may not be a PDF. Content-Type: {content_type}")
                
                # Get the filename from URL or Content-Disposition header
                filename = None
                
                # Try to get filename from Content-Disposition header
                if 'Content-Disposition' in response.headers:
                    cd = response.headers['Content-Disposition']
                    matches = re.findall(r'filename="?([^"]+)"?', cd)
                    if matches:
                        filename = matches[0]
                
                # If no filename from header, get from URL
                if not filename:
                    parsed_url = urlparse(url)
                    filename = os.path.basename(parsed_url.path) or "downloaded_file.pdf"
                
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
                    
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(response.content)
                    return tmp.name, filename
            
            # If we hit a rate limit, wait before retry
            elif response.status_code in (429, 503):
                print(f"Rate limited (status code {response.status_code}). Waiting before retry...")
                time.sleep(2 * (attempt + 1))  # Progressive backoff
            else:
                print(f"Failed to download PDF from {url}. Status code: {response.status_code}")
                # If it's not a retriable error, don't try again
                if response.status_code not in (408, 500, 502, 503, 504):
                    break
                time.sleep(1)
                
        except requests.exceptions.RequestException as e:
            print(f"Request error downloading PDF from {url}: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"Error downloading PDF from URL {url}: {e}")
            break
    
    return None, None

def extract_pdf_links_from_webpage(url: str) -> List[str]:
    """Extract PDF links from a webpage.
    
    Args:
        url: URL of the webpage
        
    Returns:
        List of PDF URLs found on the page
    """
    pdf_links = []
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Find links ending with .pdf
            pdf_pattern = r'href=[\'"]?([^\'" >]+\.pdf)[\'"]?'
            matches = re.findall(pdf_pattern, response.text, re.IGNORECASE)
            
            base_url = urlparse(url)
            base_domain = f"{base_url.scheme}://{base_url.netloc}"
            
            for match in matches:
                # Handle relative URLs
                if match.startswith('http'):
                    pdf_links.append(match)
                elif match.startswith('/'):
                    pdf_links.append(f"{base_domain}{match}")
                else:
                    path = os.path.dirname(base_url.path)
                    pdf_links.append(f"{base_domain}{path}/{match}")
    
    except Exception as e:
        print(f"Error extracting PDF links from {url}: {e}")
    
    return pdf_links