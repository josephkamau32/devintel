"""Text chunking utilities using tiktoken."""

import tiktoken
from typing import List, Tuple

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_token_count(text: str, encoding_name: str = "cl100k_base") -> int:
    """Get token count for text using tiktoken."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def chunk_text(
    text: str,
    chunk_size: int = settings.chunk_size,
    chunk_overlap: int = settings.chunk_overlap,
    encoding_name: str = "cl100k_base",
) -> List[Tuple[str, int, int]]:
    """
    Chunk text into overlapping segments based on token count.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens
        encoding_name: Tiktoken encoding name
        
    Returns:
        List of tuples (chunk_text, start_char, end_char)
    """
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    
    if len(tokens) <= chunk_size:
        return [(text, 0, len(text))]
    
    chunks = []
    start_idx = 0
    
    while start_idx < len(tokens):
        # Get chunk tokens
        end_idx = min(start_idx + chunk_size, len(tokens))
        chunk_tokens = tokens[start_idx:end_idx]
        
        # Decode back to text
        chunk_text = encoding.decode(chunk_tokens)
        
        # Find character positions (approximate)
        start_char = len(encoding.decode(tokens[:start_idx]))
        end_char = len(encoding.decode(tokens[:end_idx]))
        
        chunks.append((chunk_text, start_char, end_char))
        
        # Move to next chunk with overlap
        if end_idx == len(tokens):
            break
        start_idx += chunk_size - chunk_overlap
    
    logger.info(f"Chunked text into {len(chunks)} chunks (total tokens: {len(tokens)})")
    return chunks


def smart_chunk_code(
    code: str,
    file_path: str,
    chunk_size: int = settings.chunk_size,
    chunk_overlap: int = settings.chunk_overlap,
) -> List[str]:
    """
    Chunk code while trying to preserve structure.
    For now, falls back to token-based chunking.
    Future: Add language-specific parsing.
    """
    chunks_with_pos = chunk_text(code, chunk_size, chunk_overlap)
    return [chunk[0] for chunk in chunks_with_pos]
