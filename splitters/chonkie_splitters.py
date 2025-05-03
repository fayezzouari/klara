from chonkie import SemanticChunker

# Basic initialization with default parameters
chunker = SemanticChunker(
    embedding_model="minishlab/potion-base-8M",  # Default model
    threshold=0.5,                               # Similarity threshold (0-1) or (1-100) or "auto"
    chunk_size=512,                              # Maximum tokens per chunk
    min_sentences=1                              # Initial sentences per chunk
)

text = """First paragraph about a specific topic.
Second paragraph continuing the same topic.
Third paragraph switching to a different topic.
Fourth paragraph expanding on the new topic."""

chunks = chunker.chunk(text)

for chunk in chunks:
    print(f"Chunk text: {chunk.text}")
    print(f"Token count: {chunk.token_count}")
    print(f"Number of sentences: {len(chunk.sentences)}")