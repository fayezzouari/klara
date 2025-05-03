import os
import tempfile
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from langchain_community.document_loaders.pdf import PyPDFLoader
from chromadb.utils import embedding_functions
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import chromadb

# Import configuration settings
from config import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_CHUNKER_MODEL,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_THRESHOLD,
    DEFAULT_MIN_SENTENCES,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_LLM_MODEL,
    DEFAULT_RESULTS_COUNT
)

# Import our document splitter
from splitters.document_splitter import DocumentSplitter

# Load environment variables
load_dotenv()

class DocumentProcessor:
    def __init__(self, 
                 embedding_model: str = DEFAULT_EMBEDDING_MODEL,
                 chunker_model: str = DEFAULT_CHUNKER_MODEL,
                 chunk_size: int = DEFAULT_CHUNK_SIZE,
                 chunk_threshold: float = DEFAULT_CHUNK_THRESHOLD,
                 min_sentences: int = DEFAULT_MIN_SENTENCES,
                 collection_name: str = DEFAULT_COLLECTION_NAME,
                 llm_model: str = DEFAULT_LLM_MODEL):
        """Initialize the document processor with models and parameters."""
        # Initialize the document splitter
        self.splitter = DocumentSplitter(
            embedding_model=chunker_model,
            threshold=chunk_threshold,
            chunk_size=chunk_size,
            min_sentences=min_sentences
        )
        
        # Initialize ChromaDB with embedding function
        self.client = chromadb.Client()
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
        # Store configuration
        self.llm_model = llm_model
        
        # Initialize LLM for response generation
        self.setup_llm()
    
    def setup_llm(self):
        """Setup the LLM for response generation using Groq."""
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model=self.llm_model
        )
    
    def parse_pdf(self, pdf_path: str, original_filename: str = None) -> List[Dict]:
        """Parse a PDF file and return documents with metadata."""
        try:
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Extract document name and title from original_filename if provided

            doc_name = os.path.basename(original_filename) if original_filename else os.path.basename(pdf_path)
            doc_title = os.path.splitext(doc_name)[0]
                
            print(f"Using document name: {doc_name}, title: {doc_title}")
            
            # Store the absolute path to the original file if it exists
            file_path = os.path.abspath(pdf_path)
            
            # Enrich metadata
            for doc in documents:
                doc.metadata["document_name"] = doc_name
                doc.metadata["document_title"] = doc_title
                doc.metadata["file_path"] = file_path  # Add file path to metadata
                
            return documents
            
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return []
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Chunk documents using semantic chunker."""
        chunked_docs = []
        
        for doc in documents:
            page_content = doc.page_content
            metadata = doc.metadata
            
            if not page_content.strip():
                continue
            
            # Use our document splitter to chunk the content    
            chunks = self.splitter.split_text(page_content)
            
            for chunk in chunks:
                chunked_docs.append({
                    "id": f"{metadata['document_name']}_p{metadata['page']}_c{chunk['chunk_id']}",
                    "text": chunk["text"],
                    "metadata": {
                        "document_name": metadata["document_name"],
                        "document_title": metadata["document_title"],
                        "page_number": metadata["page"] + 1,  # Make page numbers 1-indexed
                        "chunk_id": chunk["chunk_id"],
                        "token_count": chunk["token_count"],
                        "file_path": metadata.get("file_path", "")  # Include file path in chunk metadata
                    }
                })
        
        return chunked_docs
    
    def store_chunks(self, chunked_docs: List[Dict]) -> bool:
        """Store document chunks in ChromaDB."""
        try:
            if not chunked_docs:
                return False
                
            ids = [doc["id"] for doc in chunked_docs]
            texts = [doc["text"] for doc in chunked_docs]
            metadatas = [doc["metadata"] for doc in chunked_docs]
            
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            return True
            
        except Exception as e:
            print(f"Error storing chunks: {e}")
            return False
    
    def process_pdf(self, pdf_path: str, original_filename: str = None) -> bool:
        """Complete process to parse, chunk, and store PDF."""
        documents = self.parse_pdf(pdf_path, original_filename)
        if not documents:
            return False
            
        chunked_docs = self.chunk_documents(documents)
        if not chunked_docs:
            return False
            
        return self.store_chunks(chunked_docs)
    
    def query_documents(self, query: str, n_results: int = DEFAULT_RESULTS_COUNT) -> Dict:
        """Query the vector database for relevant chunks."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            return results
        except Exception as e:
            print(f"Error querying documents: {e}")
            return None
    
    def format_context_from_results(self, results: Dict) -> str:
        """Format query results into context for the LLM."""
        if not results or not results['documents'][0]:
            return "No relevant documents found."
        
        context = ""
        source_map = {}  # Map document titles to source numbers
        current_source = 1
        
        # First, assign source numbers to each unique document
        for metadata in results['metadatas'][0]:
            doc_title = metadata['document_title']
            if doc_title not in source_map:
                source_map[doc_title] = current_source
                current_source += 1
        
        # Format context with source numbers
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            doc_title = metadata['document_title']
            page_num = metadata['page_number']
            source_num = source_map[doc_title]
            
            context += f"Source: {source_num} ({doc_title})\n"
            context += f"Page: {page_num}\n"
            context += f"Content: {doc}\n\n"
        
        # Store the source mapping for later use
        self.source_map = source_map
        
        return context

    def generate_response(self, query: str, n_results: int = DEFAULT_RESULTS_COUNT) -> str:
        """Generate a response to a query using retrieved documents and LLM."""
        results = self.query_documents(query, n_results)
        if not results or not results['documents'][0]:
            return "I couldn't find any relevant information to answer your question."
        
        # Format context from retrieved documents
        context = self.format_context_from_results(results)
        
        # Get source document information
        source_map = getattr(self, 'source_map', {})
        sources_info = []
        
        for metadata in results['metadatas'][0]:
            doc_title = metadata['document_title']
            source_num = source_map.get(doc_title, 0)
            
            # Skip if we've already added this source
            if any(src['source_num'] == source_num for src in sources_info):
                continue
                
            sources_info.append({
                "title": doc_title,
                "file_path": metadata.get("file_path", ""),
                "document_name": metadata.get("document_name", ""),
                "source_num": source_num
            })
        
        # Sort sources by source number
        sources_info.sort(key=lambda x: x['source_num'])
        
        # Create prompt template with new citation format instructions
        prompt = ChatPromptTemplate.from_template(
            """You are a helpful assistant that answers questions based on the provided documents.
            
            When citing information, use this exact format:
            - Format citations as [N-P] where N is the source number and P is the page number
            - For example, [1-3] refers to source #1, page 3
            - Always put citations in square brackets like [1-1], [2-6], etc.
            - Include citations for every piece of information you provide
            - At the end of your response, include a "Sources:" section that lists all source numbers and their document titles
            
            Context:
            {context}
            
            Question: {question}
            
            Answer the question based on the context. If you don't know the answer, say so.
            Use the format [N-P] for citations, where N is the source number and P is the page number.
            At the end, add a "Sources:" section listing all source numbers and their document names."""
        )
        
        # Create chain
        chain = (
            {"context": lambda x: context, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Run the chain
        response = chain.invoke(query)
        
        # If sources weren't included, append them manually
        if "Sources:" not in response and sources_info:
            sources_text = "\n\nSources:\n"
            for src in sources_info:
                sources_text += f"[{src['source_num']}] {src['title']}\n"
            response += sources_text
        
        # Store the sources metadata for HTML processing
        self.last_sources = sources_info
        
        return response
        
    def get_last_sources_info(self):
        """Return metadata about the last sources used in a response."""
        if hasattr(self, 'last_sources'):
            return self.last_sources
        return []

    def save_temp_pdf(self, pdf_file) -> Optional[str]:
        """Save an uploaded PDF to a temporary file."""
        try:
            # Handle Gradio file object which returns a tuple of (file_name, file_path)
            if isinstance(pdf_file, tuple) and len(pdf_file) == 2:
                file_path = pdf_file[1]
                # If the file already exists on disk, return its path
                if os.path.exists(file_path):
                    return file_path
            
            # For handling direct file uploads or file-like objects
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                if hasattr(pdf_file, 'read'):
                    # If it's a file-like object with read method
                    tmp.write(pdf_file.read())
                elif isinstance(pdf_file, bytes):
                    # If it's raw bytes
                    tmp.write(pdf_file)
                elif isinstance(pdf_file, str):
                    # If it's a file path
                    if os.path.exists(pdf_file):
                        with open(pdf_file, 'rb') as f:
                            tmp.write(f.read())
                    else:
                        # If it's a string content
                        tmp.write(pdf_file.encode())
                else:
                    # For Gradio newer versions, the file is directly provided as a path
                    return pdf_file
                    
                return tmp.name
        except Exception as e:
            print(f"Error saving temporary PDF: {e}")
            return None