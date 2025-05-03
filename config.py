"""Configuration settings for the PDF Document QA System."""

# Document processing settings
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CHUNKER_MODEL = "minishlab/potion-base-8M"
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_THRESHOLD = 0.5
DEFAULT_MIN_SENTENCES = 1
DEFAULT_COLLECTION_NAME = "document_chunks"

# LLM settings
DEFAULT_LLM_MODEL = "llama-3.3-70b-versatile"

# Query settings
DEFAULT_RESULTS_COUNT = 3