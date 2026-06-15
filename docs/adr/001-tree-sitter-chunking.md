# ADR-001: Tree-Sitter AST Chunking Over Naive Character Splitting

## Status
Accepted

## Context
Traditional RAG pipelines use fixed-size character or token chunking, which splits code at arbitrary points. This destroys syntactic context, making it impossible for LLMs to understand:
- Complete function signatures
- Class hierarchies
- Proper indentation and scoping

## Decision
We use Tree-Sitter for language-aware AST parsing to extract semantic code blocks (functions, classes, methods) and chunk at logical boundaries.

## Consequences
- **Positive**: LLM receives complete syntactic context
- **Positive**: Reduced hallucination in code modifications
- **Negative**: Adds dependency on Tree-Sitter language grammars
- **Negative**: Slightly more complex than naive chunking

## Alternatives Considered
1. Character-based chunking - rejected due to context loss
2. Token-based with overlap - rejected due to arbitrary splits
3. Custom parser per language - rejected due to maintenance overhead

## Implementation
- `app/utils/tree_sitter_chunking.py` implements the chunking logic
- Supports Python, JavaScript, TypeScript, Go, Java, Rust
- Uses tiktoken for accurate token counting