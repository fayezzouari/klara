import os
import gradio as gr
from core import DocumentProcessor
from utils.markdown_formatter import convert_citations_to_markdown
from utils.url_utils import download_pdf, is_valid_url, is_pdf_url, extract_pdf_links_from_webpage

# Initialize the document processor
processor = DocumentProcessor()

def process_multiple_files(pdf_files, pdf_urls):
    """Process multiple PDF files and URLs."""
    if not pdf_files and not (pdf_urls and pdf_urls.strip()):
        return "No files or URLs provided. Please upload files or enter URLs."
    
    results = []
    processed_count = 0
    
    # Process uploaded files
    if pdf_files:
        for pdf_file in pdf_files:
            try:
                # Extract original filename
                original_filename = None
                if isinstance(pdf_file, tuple):
                    if len(pdf_file) >= 1:
                        original_filename = os.path.basename(pdf_file[0])
                elif isinstance(pdf_file, dict) and 'name' in pdf_file:
                    original_filename = pdf_file['name']
                elif hasattr(pdf_file, 'name'):
                    original_filename = pdf_file.name
                
                if not original_filename:
                    original_filename = f"uploaded_document_{processed_count}.pdf"
                
                # Save and process the file
                pdf_path = processor.save_temp_pdf(pdf_file)
                if pdf_path:
                    success = processor.process_pdf(pdf_path, original_filename)
                    
                    # Clean up the temporary file
                    if os.path.exists(pdf_path) and "tmp" in pdf_path:
                        os.unlink(pdf_path)
                    
                    if success:
                        results.append(f"✅ PDF '{original_filename}' successfully processed")
                        processed_count += 1
                    else:
                        results.append(f"❌ Failed to process '{original_filename}'")
            except Exception as e:
                results.append(f"❌ Error processing file: {str(e)}")
    
    # Process URLs
    if pdf_urls and pdf_urls.strip():
        urls = [url.strip() for url in pdf_urls.split('\n') if url.strip()]
        
        # Collect all PDF URLs, including those extracted from web pages
        all_pdf_urls = []
        for url in urls:
            if not is_valid_url(url):
                results.append(f"❌ Invalid URL: '{url}'")
                continue
                
            # If URL is directly a PDF, add it
            if is_pdf_url(url):
                all_pdf_urls.append(url)
            else:
                # Try to extract PDF links from the webpage
                extracted_links = extract_pdf_links_from_webpage(url)
                if extracted_links:
                    results.append(f"ℹ️ Found {len(extracted_links)} PDF links on webpage '{url}'")
                    all_pdf_urls.extend(extracted_links)
                else:
                    results.append(f"⚠️ No PDF links found on webpage '{url}'")
        
        # Process all PDF URLs
        for url in all_pdf_urls:
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
    
    # Convert the response to HTML with clickable links
    html_response = convert_citations_to_markdown(text_response, sources_info)
    
    return html_response

# Create the Gradio interface
with gr.Blocks(title="PDF Document QA System") as demo:
    gr.Markdown("# PDF Document QA System")
    gr.Markdown("""
    This application allows you to:
    1. Upload multiple PDF documents or provide URLs to PDF files for processing
    2. Query the documents to get relevant information with clickable source links
    """)
    
    # Document upload and processing section
    with gr.Tab("Upload & Process Documents"):
        gr.Markdown("## Upload PDF Documents")
        gr.Markdown("""
        You can:
        - Upload multiple PDF files at once
        - Enter URLs directly to PDF files (one per line)
        - Enter URLs to webpages containing PDF links (the system will extract and process them)
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                pdf_files = gr.File(label="Upload PDF Files", file_types=[".pdf"], file_count="multiple")
            
            with gr.Column(scale=1):
                pdf_urls = gr.Textbox(
                    label="PDF URLs or Webpages with PDFs (one per line)", 
                    lines=5, 
                    placeholder="https://example.com/document1.pdf\nhttps://example.com/documents-page"
                )
        
        process_button = gr.Button("Process Documents", variant="primary")
        process_output = gr.Textbox(label="Processing Status", lines=10)
        
        process_button.click(
            fn=process_multiple_files,
            inputs=[pdf_files, pdf_urls],
            outputs=process_output
        )
    
    # Document querying section
    with gr.Tab("Query Documents"):
        gr.Markdown("## Ask Questions About Your Documents")
        gr.Markdown("""Enter a query to get information from your processed documents.
        
The citations [p.X] and document names in the Sources section are clickable links to the original PDF.""")
        
        query_input = gr.Textbox(label="Your Question", lines=2, placeholder="What does the document say about...?")
        query_button = gr.Button("Ask", variant="primary")
        
        # Use HTML component for better rendering of links
        response_output = gr.HTML(label="Answer")
        
        query_button.click(
            fn=query_documents,
            inputs=query_input,
            outputs=response_output
        )

if __name__ == "__main__":
    # Check if .env file exists with GROQ_API_KEY
    if not os.path.exists(".env") or "GROQ_API_KEY" not in open(".env").read():
        print("Warning: .env file missing or GROQ_API_KEY not set.")
        print("Please create a .env file with GROQ_API_KEY=your_api_key")
    
    # Launch with share=True to make temporary links accessible
    demo.launch()