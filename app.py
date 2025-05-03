import os
import gradio as gr
from core import DocumentProcessor

# Initialize the document processor
processor = DocumentProcessor()

def process_pdf(pdf_file):
    """Process an uploaded PDF file."""
    if pdf_file is None:
        return "No file uploaded. Please upload a PDF file."
    
    try:
        # Extract original filename from Gradio file object
        original_filename = None
        
        # Different versions of Gradio return different formats
        if isinstance(pdf_file, tuple):
            if len(pdf_file) >= 1:
                original_filename = os.path.basename(pdf_file[0])
        elif isinstance(pdf_file, dict) and 'name' in pdf_file:
            original_filename = pdf_file['name']
        elif hasattr(pdf_file, 'name'):
            original_filename = pdf_file.name
            
        # Use a default name if we couldn't extract one
        if not original_filename:
            original_filename = "uploaded_document.pdf"
            
        print(f"Processing file with original name: {original_filename}")
            
        # Save the uploaded file temporarily
        pdf_path = processor.save_temp_pdf(pdf_file)
        if pdf_path is None:
            return "Failed to save the uploaded file."
        
        # Process the PDF with original filename
        documents = processor.parse_pdf(pdf_path, original_filename)
        if not documents:
            return "Failed to parse the PDF. The file might be empty or corrupted."
            
        chunked_docs = processor.chunk_documents(documents)
        if not chunked_docs:
            return "Failed to chunk the PDF content."
            
        success = processor.store_chunks(chunked_docs)
        
        # Clean up the temporary file
        try:
            if os.path.exists(pdf_path) and os.path.isfile(pdf_path) and "tmp" in pdf_path:
                os.unlink(pdf_path)
        except Exception as e:
            print(f"Warning: Could not remove temporary file: {e}")
        
        if success:
            return f"PDF '{original_filename}' successfully processed and stored in the vector database."
        else:
            return "Failed to store the processed PDF chunks. Please try again."
            
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return f"Error processing PDF: {str(e)}"

def query_documents(query_text):
    """Query the processed documents."""
    if not query_text.strip():
        return "Please enter a query."
    
    response = processor.generate_response(query_text)
    return response

# Create the Gradio interface
with gr.Blocks(title="PDF Document QA System") as demo:
    gr.Markdown("# PDF Document QA System")
    gr.Markdown("""
    This application allows you to:
    1. Upload PDF documents for processing
    2. Query the documents to get relevant information
    """)
    
    # Document upload and processing section
    with gr.Tab("Upload & Process Documents"):
        gr.Markdown("## Upload PDF Documents")
        gr.Markdown("Upload a PDF document to process and store in the vector database.")
        
        with gr.Row():
            pdf_file = gr.File(label="PDF File", file_types=[".pdf"])
            process_button = gr.Button("Process PDF")
        
        process_output = gr.Textbox(label="Processing Status", lines=2)
        
        process_button.click(
            fn=process_pdf,
            inputs=[pdf_file],
            outputs=process_output
        )
    
    # Document querying section
    with gr.Tab("Query Documents"):
        gr.Markdown("## Ask Questions About Your Documents")
        gr.Markdown("Enter a query to get information from your processed documents.")
        
        query_input = gr.Textbox(label="Your Question", lines=2, placeholder="What does the document say about...?")
        query_button = gr.Button("Ask")
        response_output = gr.Textbox(label="Answer", lines=10)
        
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
    
    demo.launch()