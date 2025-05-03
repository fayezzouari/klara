from typing import List, Dict, Any
from chonkie import SemanticChunker

class DocumentSplitter:
    """Document splitter class that uses chonkie's SemanticChunker."""
    
    def __init__(self, 
                 embedding_model: str = "minishlab/potion-base-8M",
                 threshold: float = 0.5,
                 chunk_size: int = 512,
                 min_sentences: int = 1):
        """Initialize the document splitter with parameters.
        
        Args:
            embedding_model: Model name for semantic chunking
            threshold: Similarity threshold for chunking (0-1)
            chunk_size: Maximum tokens per chunk
            min_sentences: Minimum sentences per chunk
        """
        self.chunker = SemanticChunker(
            embedding_model=embedding_model,
            threshold=threshold,
            chunk_size=chunk_size,
            min_sentences=min_sentences
        )
    
    def split_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into semantic chunks.
        
        Args:
            text: Text content to split
            
        Returns:
            List of dictionaries with chunk info
        """
        if not text or not text.strip():
            return []
            
        chunks = self.chunker.chunk(text)
        
        # Convert chunks to a list of dictionaries
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "text": chunk.text,
                "token_count": chunk.token_count,
                "sentence_count": len(chunk.sentences),
                "chunk_id": i
            })
            
        return result