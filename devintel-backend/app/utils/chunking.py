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
    """
    import re
    from app.utils.tree_sitter_chunking import chunk_code_with_tree_sitter
    
    # Try Tree-Sitter first
    ts_chunks = chunk_code_with_tree_sitter(code, file_path, chunk_size)
    if ts_chunks:
        # Check if we need further token-based chunking for any large ts_chunks
        final_chunks = []
        for tc in ts_chunks:
            if get_token_count(tc) > chunk_size:
                sub_chunks = chunk_text(tc, chunk_size, chunk_overlap)
                final_chunks.extend([sc[0] for sc in sub_chunks])
            else:
                final_chunks.append(tc)
        
        logger.info(f"Tree-Sitter chunked {file_path} into {len(final_chunks)} chunks")
        return final_chunks

    # Fallback to regex-based splitting
    ext = file_path.split('.')[-1].lower() if '.' in file_path else ""
    
    # Define splitting patterns per language
    # We want to split BEFORE these keywords to keep them at the start of chunks
    patterns = {
        "py": r"\n(?=class\s+|def\s+)",
        "js": r"\n(?=function\s+|class\s+|const\s+\w+\s*=\s*(async\s+)?(\(.*\)|.*)=>|export\s+)",
        "ts": r"\n(?=function\s+|class\s+|interface\s+|type\s+|const\s+\w+\s*=\s*(async\s+)?(\(.*\)|.*)=>|export\s+)",
        "tsx": r"\n(?=function\s+|class\s+|interface\s+|type\s+|const\s+\w+\s*=\s*(async\s+)?(\(.*\)|.*)=>|export\s+)",
        "jsx": r"\n(?=function\s+|class\s+|const\s+\w+\s*=\s*(async\s+)?(\(.*\)|.*)=>|export\s+)",
    }
    
    pattern = patterns.get(ext)
    
    if not pattern:
        # Fallback to token-based chunking for unsupported languages
        chunks_with_pos = chunk_text(code, chunk_size, chunk_overlap)
        return [chunk[0] for chunk in chunks_with_pos]
    
    # Split code by logical blocks
    blocks = re.split(pattern, code)
    
    final_chunks = []
    current_chunk = ""
    current_tokens = 0
    
    for block in blocks:
        block_tokens = get_token_count(block)
        
        # If a single block is larger than chunk_size, split it normally
        if block_tokens > chunk_size:
            # Add current_chunk if not empty
            if current_chunk:
                final_chunks.append(current_chunk)
                current_chunk = ""
                current_tokens = 0
            
            # Sub-chunk the large block
            sub_chunks = chunk_text(block, chunk_size, chunk_overlap)
            final_chunks.extend([sc[0] for sc in sub_chunks])
            continue
            
        # If adding block exceeds size, save current and start new
        if current_tokens + block_tokens > chunk_size:
            final_chunks.append(current_chunk)
            # Start next chunk with overlap - simple approach: overlap current block with previous if possible
            # For simplicity in code structure preserving, we just start fresh with the block
            current_chunk = block
            current_tokens = block_tokens
        else:
            current_chunk += block
            current_tokens += block_tokens
            
    if current_chunk:
        final_chunks.append(current_chunk)
        
    logger.info(f"Smart-chunked {file_path} into {len(final_chunks)} chunks")
    return final_chunks
