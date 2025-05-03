import os
import tempfile
from typing import Dict, List, Any, Optional, Tuple
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

# Import structured data processor
from utils.structured_data_processor import StructuredDataProcessor

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
        
        # Initialize structured data processor
        self.structured_processor = StructuredDataProcessor(max_rows_per_chunk=50)
        
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
                doc.metadata["document_type"] = "pdf"  # Mark as PDF
                
            return documents
            
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return []
    
    def process_structured_file(self, file_path: str, original_filename: str = None) -> List[Dict]:
        """Process a CSV or Excel file and return structured data chunks."""
        try:
            # Use the structured data processor to handle the file
            structured_chunks = self.structured_processor.process_file(
                file_path, 
                original_filename=original_filename
            )
            
            # Convert to document format compatible with our system
            documents = []
            
            for chunk in structured_chunks:
                # Get absolute file path
                abs_file_path = os.path.abspath(file_path)
                
                # Add to documents list with proper metadata
                doc_dict = {
                    "page_content": chunk["text"],
                    "metadata": {
                        "document_name": chunk["metadata"]["document_name"],
                        "document_title": chunk["metadata"]["document_title"],
                        "file_path": abs_file_path,
                        "document_type": "structured_data",  # Mark as structured data
                        "chunk_type": chunk["metadata"]["chunk_type"],
                        # Add page as 1 for summary and chunk_idx+1 for data chunks
                        "page": 1 if chunk["metadata"]["chunk_type"] == "summary" else chunk["metadata"]["chunk_idx"] + 1
                    }
                }
                
                # Add additional metadata for data chunks
                if chunk["metadata"]["chunk_type"] == "data_chunk":
                    doc_dict["metadata"]["row_start"] = chunk["metadata"]["row_start"]
                    doc_dict["metadata"]["row_end"] = chunk["metadata"]["row_end"]
                    doc_dict["metadata"]["total_rows"] = chunk["metadata"]["total_rows"]
                
                # Create a document object (with dict-like access)
                class Document:
                    def __init__(self, data):
                        self.__dict__.update(data)
                
                doc = type('Document', (), doc_dict)
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Error processing structured file: {e}")
            return []
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Chunk documents using semantic chunker."""
        chunked_docs = []
        
        for doc in documents:
            page_content = doc.page_content
            metadata = doc.metadata
            
            if not page_content.strip():
                continue
            
            # Skip chunking for structured data - already chunked appropriately
            if metadata.get("document_type") == "structured_data":
                chunked_docs.append({
                    "id": f"{metadata['document_name']}_{metadata.get('chunk_type', '')}_{metadata['page']}",
                    "text": page_content,
                    "metadata": metadata
                })
                continue
                
            # Use our document splitter to chunk the content for PDFs    
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
                        "file_path": metadata.get("file_path", ""),  # Include file path in chunk metadata
                        "document_type": metadata.get("document_type", "pdf")
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
    
    def process_file(self, file_path: str, original_filename: str = None) -> bool:
        """Process any supported file (PDF, CSV, Excel) and store in vector DB."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.process_pdf(file_path, original_filename)
        elif file_ext in ['.csv', '.xlsx', '.xls']:
            documents = self.process_structured_file(file_path, original_filename)
            if not documents:
                return False
                
            chunked_docs = self.chunk_documents(documents)
            if not chunked_docs:
                return False
                
            return self.store_chunks(chunked_docs)
        else:
            print(f"Unsupported file format: {file_ext}")
            return False

    def query_documents(self, query: str, n_results: int = DEFAULT_RESULTS_COUNT) -> Dict:
        try:
            # Increase the number of results to ensure we get a diverse set of documents
            enhanced_n_results = n_results * 3
            
            results = self.collection.query(
                query_texts=[query],
                n_results=enhanced_n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # If we have too few results, return what we have
            if not results or not results['documents'] or not results['documents'][0]:
                return results
                
            # Post-process results to ensure diversity across documents
            processed_results = self._ensure_document_diversity(results, n_results)
            return processed_results
            
        except Exception as e:
            print(f"Error querying documents: {e}")
            return None
            
    def _ensure_document_diversity(self, results: Dict, target_n_results: int) -> Dict:
        """Process query results to ensure diversity across different documents.
        
        This helps ensure we get context from multiple documents, not just the most similar chunks
        from a single document.
        """
        if not results or not results['documents'] or not results['documents'][0]:
            return results
            
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results.get('distances', [[]])[0]
        
        # Group by document title
        doc_groups = {}
        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            doc_title = meta.get('document_title', '')
            if doc_title not in doc_groups:
                doc_groups[doc_title] = []
                
            doc_groups[doc_title].append({
                'document': doc,
                'metadata': meta,
                'distance': dist,
                'index': i
            })
        
        # Sort each group by relevance (distance)
        for title in doc_groups:
            doc_groups[title].sort(key=lambda x: x['distance'])
        
        # Take the most relevant chunks from each document in a round-robin fashion
        selected_indices = []
        doc_titles = list(doc_groups.keys())
        
        # First take the best result from each document
        for title in doc_titles:
            if doc_groups[title]:
                selected_indices.append(doc_groups[title].pop(0)['index'])
        
        # Then continue round-robin until we have enough results
        while len(selected_indices) < target_n_results and any(doc_groups.values()):
            for title in doc_titles:
                if doc_groups[title]:
                    selected_indices.append(doc_groups[title].pop(0)['index'])
                    if len(selected_indices) >= target_n_results:
                        break
        
        # Sort by original index to maintain order
        selected_indices.sort()
        
        # Create new results with selected indices
        new_results = {
            'documents': [[documents[i] for i in selected_indices]],
            'metadatas': [[metadatas[i] for i in selected_indices]],
        }
        
        if distances:
            new_results['distances'] = [[distances[i] for i in selected_indices]]
            
        return new_results

    def generate_response(self, query: str, n_results: int = DEFAULT_RESULTS_COUNT) -> str:
        """Generate a response to a query using retrieved documents and LLM."""
        # Increase the default number of results to get context from more documents
        effective_n_results = max(n_results, DEFAULT_RESULTS_COUNT * 2)
        
        results = self.query_documents(query, effective_n_results)
        if not results or not results['documents'][0]:
            return "I couldn't find any relevant information to answer your question."
        
        # Format context from retrieved documents
        context = self.format_context_from_results(results)
        
        # Get source document information
        source_map = getattr(self, 'source_map', {})
        sources_info = []
        
        # Get unique document titles
        document_titles = set()
        for metadata in results['metadatas'][0]:
            document_titles.add(metadata['document_title'])
            
        print(f"Retrieved context from {len(document_titles)} different documents")
        
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
            - Try to use information from multiple documents when appropriate
            - At the end of your response, include a "Sources:" section that lists all source numbers and their document titles
            - If the one source is sufficient, you can just use that one source, but still include the "Sources:" section
            - If the rest of the sources are not relevant, you can skip them in the answer.
            - Present a well-structured response with clear headings when appropriate.
            - For CSV/Excel data, reference specific rows or data points when appropriate.
            - If the query asks about numerical data, include relevant statistics.
            - Do not make up or infer information that isn't in the contexts.
            - if you don't have enough information, avoid mentioning it in the answer and try to improvise.
            You are an AI assistant tasked with answering questions based on the provided document contexts. 
            Your goal is to provide accurate, informative, and helpful responses based ONLY on the information in the contexts.
            Context:
            {context}
            
            Question: {question}
            
            Answer the question based on the context. If you don't know the answer, say so.
            Use the format [N-P] for citations, where N is the source number and P is the page number.
            At the end, add a "Sources:" section listing all source numbers and their document names.
            Make sure to include information from all relevant documents in your answer."""
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
            # Handle different document types
            if metadata.get('document_type') == 'structured_data':
                page_num = metadata.get('page', 1)
                chunk_type = metadata.get('chunk_type', 'data')
                
                if chunk_type == 'summary':
                    context += f"Source: {source_map[doc_title]} ({doc_title} - Summary)\n"
                else:
                    context += f"Source: {source_map[doc_title]} ({doc_title} - Data Section {page_num})\n"
                    
                if 'row_start' in metadata and 'row_end' in metadata:
                    context += f"Rows: {metadata['row_start']}-{metadata['row_end']}\n"
                
                context += f"Content: {doc}\n\n"
            else:
                # Regular PDF document
                page_num = metadata.get('page_number', 1)
                context += f"Source: {source_map[doc_title]} ({doc_title})\n"
                context += f"Page: {page_num}\n"
                context += f"Content: {doc}\n\n"
        
        # Store the source mapping for later use
        self.source_map = source_map
        
        return context
        
    def save_temp_file(self, file_obj) -> Optional[Tuple[str, str]]:
        """Save an uploaded file to a temporary location."""
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