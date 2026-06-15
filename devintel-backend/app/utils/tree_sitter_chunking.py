from typing import Optional

import tiktoken
import tree_sitter_language_pack as tslp
from tree_sitter import Language, Node, Parser


# Global tokenizer for consistent token counting
_encoding = tiktoken.get_encoding("cl100k_base")


def get_language_for_extension(ext: str) -> Optional[str]:
    mapping = {
        "py": "python",
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "tsx",
        "go": "go",
        "java": "java",
        "rs": "rust",
        "rb": "ruby",
        "cpp": "cpp",
        "c": "c",
    }
    return mapping.get(ext.lower())

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    if not text:
        return 0
    return len(_encoding.encode(text))


def chunk_code_with_tree_sitter(code: str, file_path: str, max_tokens: int = 700) -> list[str]:
    """
    Lossless semantic chunking.
    Uses Tree-Sitter to find logical split points but ensures 100% of code is preserved.
    Uses actual token counting for accuracy.
    """
    ext = file_path.split('.')[-1].lower() if '.' in file_path else ""
    lang_name = get_language_for_extension(ext)

    if not lang_name:
        return [code] if code.strip() else []

    try:
        language = Language(tslp.get_binding(lang_name))
        parser = Parser(language)
        tree = parser.parse(bytes(code, "utf8"))
    except Exception:
        return [code] if code.strip() else []

    # 1. Identify all semantic split points
    split_offsets: set[int] = {0, len(code)}

    target_types = {
        "python": ["function_definition", "class_definition"],
        "javascript": ["function_declaration", "class_declaration", "method_definition"],
        "typescript": ["function_declaration", "class_declaration", "method_definition", "interface_declaration", "type_alias_declaration"],
        "tsx": ["function_declaration", "class_declaration", "method_definition", "interface_declaration", "type_alias_declaration"],
        "go": ["function_declaration", "method_declaration", "type_declaration"],
        "java": ["class_declaration", "method_declaration"],
        "rust": ["function_item", "struct_item", "enum_item", "impl_item", "trait_item"],
    }

    current_lang_targets = target_types.get(lang_name, [])

    def find_split_points(node: Node):
        if node.type in current_lang_targets:
            split_offsets.add(node.start_byte)
            split_offsets.add(node.end_byte)

        for child in node.children:
            find_split_points(child)

    find_split_points(tree.root_node)

    sorted_offsets = sorted(list(split_offsets))

    # 2. Slice the code into initial segments
    segments = []
    for i in range(len(sorted_offsets) - 1):
        start = sorted_offsets[i]
        end = sorted_offsets[i+1]
        if start < end:
            segment = code[start:end]
            if segment.strip():
                segments.append(segment)
            elif segments:
                segments[-1] += segment
            else:
                segments.append(segment)

    # 3. Merge segments using actual token counting
    final_chunks = []
    current_chunk = ""

    for seg in segments:
        segment_tokens = count_tokens(seg)
        current_tokens = count_tokens(current_chunk)

        if current_tokens + segment_tokens > max_tokens and current_chunk:
            final_chunks.append(current_chunk)
            current_chunk = seg
        else:
            current_chunk += seg

    if current_chunk:
        final_chunks.append(current_chunk)

    return final_chunks
