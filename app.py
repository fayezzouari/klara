import os
import gradio as gr
from core import DocumentProcessor
from file_routes import setup_file_routes
from utils.markdown_formatter import convert_citations_to_markdown
from utils.url_utils import download_pdf, is_valid_url, is_pdf_url, extract_pdf_links_from_webpage
from utils.file_service import SERVE_DIR
from file_server import start_server, FILE_DIR  # Import the file server
from dotenv import load_dotenv
from PIL import Image
import shutil  # For file copying

# Start the file server in the background
server_thread = start_server()
print("File server started on port 8089")

# Initialize the document processor
processor = DocumentProcessor()

def process_multiple_files(files, urls):
    """Process multiple files and URLs."""
    if not files and not (urls and urls.strip()):
        return "No files or URLs provided. Please upload files or enter URLs."
    
    results = []
    
    processed_count = 0
    
    # Process uploaded files
    if files:
        for file in files:
            try:
                # Extract original filename
                original_filename = None
                if isinstance(file, tuple):
                    if len(file) >= 1:
                        original_filename = os.path.basename(file[0])
                elif isinstance(file, dict) and 'name' in file:
                    original_filename = file['name']
                elif hasattr(file, 'name'):
                    original_filename = file.name
                
                if not original_filename:
                    original_filename = f"uploaded_document_{processed_count}.tmp"
                
                # Save and process the file
                file_path, saved_filename = processor.save_temp_file(file)
                if file_path:
                    # Determine file type
                    file_ext = os.path.splitext(saved_filename)[1].lower()
                    
                    if file_ext == '.pdf':
                        success = processor.process_pdf(file_path, original_filename or saved_filename)
                        file_type = "PDF"
                    elif file_ext in ['.csv', '.xlsx', '.xls']:
                        success = processor.process_file(file_path, original_filename or saved_filename)
                        file_type = "CSV" if file_ext == '.csv' else "Excel"
                    else:
                        success = False
                        file_type = "Unsupported"
                        results.append(f"❌ Unsupported file type: {file_ext}")
                        continue
                    
                    # Clean up the temporary file
                    if os.path.exists(file_path) and "tmp" in file_path:
                        os.unlink(file_path)
                    
                    if success:
                        results.append(f"✅ {file_type} file '{original_filename or saved_filename}' successfully processed")
                        processed_count += 1
                    else:
                        results.append(f"❌ Failed to process '{original_filename or saved_filename}'")
            except Exception as e:
                results.append(f"❌ Error processing file: {str(e)}")
    
    # Process URLs
    if urls and urls.strip():
        url_list = [url.strip() for url in urls.split('\n') if url.strip()]
        
        # Collect all URLs, including those for PDFs, CSVs, and Excel files
        for url in url_list:
            if not is_valid_url(url):
                results.append(f"❌ Invalid URL: '{url}'")
                continue
                
            # Determine file type based on URL
            file_ext = os.path.splitext(url.split('?')[0].split('#')[0])[1].lower()
            
            if file_ext in ['.csv', '.xlsx', '.xls']:
                # Handle structured data URLs
                try:
                    import requests
                    import tempfile
                    
                    response = requests.get(url)
                    if response.status_code == 200:
                        # Save to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                            tmp.write(response.content)
                            temp_path = tmp.name
                        
                        # Process the file
                        filename = os.path.basename(url.split('?')[0].split('#')[0])
                        success = processor.process_file(temp_path, filename)
                        
                        # Clean up
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        
                        if success:
                            file_type = "CSV" if file_ext == '.csv' else "Excel"
                            results.append(f"✅ {file_type} from URL '{url}' successfully processed as '{filename}'")
                            processed_count += 1
                        else:
                            results.append(f"❌ Failed to process file from URL '{url}'")
                    else:
                        results.append(f"❌ Failed to download file from URL '{url}': HTTP {response.status_code}")
                except Exception as e:
                    results.append(f"❌ Error processing URL '{url}': {str(e)}")
            elif is_pdf_url(url):
                # Handle PDF URLs (using existing functionality)
                try:
                    pdf_path, filename = download_pdf(url)
                    if pdf_path:
                        success = processor.process_pdf(pdf_path, filename)
                        
                        # Clean up the temporary file
                        if os.path.exists(pdf_path):
                            os.unlink(pdf_path)
                        
                        if success:
                            results.append(f"✅ PDF from URL '{url}' successfully processed as '{filename}'")
                            processed_count += 1
                        else:
                            results.append(f"❌ Failed to process PDF from URL '{url}'")
                    else:
                        results.append(f"❌ Failed to download PDF from URL '{url}'")
                except Exception as e:
                    results.append(f"❌ Error processing URL '{url}': {str(e)}")
            else:
                # Check if it's a webpage that might contain PDF links
                extracted_links = extract_pdf_links_from_webpage(url)
                if extracted_links:
                    results.append(f"ℹ️ Found {len(extracted_links)} PDF links on webpage '{url}'")
                    for pdf_url in extracted_links:
                        try:
                            pdf_path, filename = download_pdf(pdf_url)
                            if pdf_path:
                                success = processor.process_pdf(pdf_path, filename)
                                
                                # Clean up the temporary file
                                if os.path.exists(pdf_path):
                                    os.unlink(pdf_path)
                                
                                if success:
                                    results.append(f"✅ PDF from URL '{pdf_url}' successfully processed as '{filename}'")
                                    processed_count += 1
                                else:
                                    results.append(f"❌ Failed to process PDF from URL '{pdf_url}'")
                            else:
                                results.append(f"❌ Failed to download PDF from URL '{pdf_url}'")
                        except Exception as e:
                            results.append(f"❌ Error processing URL '{pdf_url}': {str(e)}")
                else:
                    results.append(f"⚠️ No processable file links found on webpage '{url}'")
    
    # Format the results
    result_text = "\n".join(results)
    summary = f"\n\nSummary: {processed_count} document(s) successfully processed."
    
    return result_text + summary

def query_documents(query_text):
    """Query the processed documents."""
    if not query_text.strip():
        return "Please enter a query."
    
    # Generate text response
    text_response = processor.generate_response(query_text)
    
    # Get the source information from the last query
    sources_info = processor.get_last_sources_info()
    
    # Convert the response to markdown with clickable links
    markdown_response = convert_citations_to_markdown(text_response, sources_info)
    
    return markdown_response

# Create the Gradio interface
with gr.Blocks(title="Document QA System") as demo:
    gr.Markdown("# Document QA System")
    gr.Markdown("""
    This application allows you to:
    1. Upload multiple documents (PDF, CSV, Excel) or provide URLs to files for processing
    2. Query the documents to get relevant information with clickable source links
    """)
    
    # Document upload and processing section
    with gr.Tab("Upload & Process Documents"):
        gr.Markdown("## Upload Documents")
        gr.Markdown("""
        You can:
        - Upload multiple files at once (PDF, CSV, Excel)
        - Enter URLs directly to files (one per line)
        - Enter URLs to webpages containing PDF links (the system will extract and process them)
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                files = gr.File(
                    label="Upload Files", 
                    file_types=[".pdf", ".csv", ".xlsx", ".xls"], 
                    file_count="multiple"
                )
            
            with gr.Column(scale=1):
                urls = gr.Textbox(
                    label="Document URLs or Webpages (one per line)", 
                    lines=5, 
                    placeholder="https://example.com/document1.pdf\nhttps://example.com/data.csv\nhttps://example.com/documents-page"
                )
        
        process_button = gr.Button("Process Documents", variant="primary")
        process_output = gr.Textbox(label="Processing Status", lines=10)
        
        process_button.click(
            fn=process_multiple_files,
            inputs=[files, urls],
            outputs=process_output
        )
    
    # Document querying section
    with gr.Tab("Query Documents"):
        gr.Markdown("## Ask Questions About Your Documents")
        gr.Markdown("""Enter a query to get information from your processed documents.
        
The citations [N-P] and document names in the Sources section are clickable links to the original documents.""")
        
        query_input = gr.Textbox(label="Your Question", lines=2, placeholder="What does the document say about...?")
        query_button = gr.Button("Ask", variant="primary")
        
        # Use Markdown component for better rendering of links
        response_output = gr.Markdown(label="Answer")
        
        query_button.click(
            fn=query_documents,
            inputs=query_input,
            outputs=response_output
        )

if __name__ == "__main__":
    load_dotenv(dotenv_path=".env", override=True)

    # Check if .env file exists with GROQ_API_KEY
    if not os.path.exists(".env") or "GROQ_API_KEY" not in open(".env").read():
        print("Warning: .env file missing or GROQ_API_KEY not set.")
        print("Please create a .env file with GROQ_API_KEY=your_api_key")
    
    # Check for required packages
    try:
        import pandas as pd
        print("Pandas is installed, CSV and Excel processing is enabled.")
    except ImportError:
        print("Warning: pandas is not installed. CSV and Excel processing will not work.")
        print("Install with: pip install pandas")
    
    # Launch with simpler configuration that works across Gradio versions
    demo.launch(
        show_error=True,
        share=True
    )