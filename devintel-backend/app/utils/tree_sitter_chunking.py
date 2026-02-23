import tree_sitter_language_pack as tslp
from tree_sitter import Language, Parser, Node
from typing import List, Optional
import os

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

def chunk_code_with_tree_sitter(code: str, file_path: str, max_tokens: int = 700) -> List[str]:
    ext = file_path.split('.')[-1].lower() if '.' in file_path else ""
    lang_name = get_language_for_extension(ext)
    
    if not lang_name:
        return []

    try:
        language = Language(tslp.get_binding(lang_name))
        parser = Parser(language)
        tree = parser.parse(bytes(code, "utf8"))
    except Exception:
        return []

    chunks = []
    
    # Simple strategy: Find top-level definitions or logical blocks
    # If a block is too large, it will be handled by the fallback chunker
    
    def collect_chunks(node: Node):
        # We look for major structural elements
        target_types = {
            "python": ["function_definition", "class_definition"],
            "javascript": ["function_declaration", "class_declaration", "method_definition", "variable_declaration"],
            "typescript": ["function_declaration", "class_declaration", "method_definition", "interface_declaration", "type_alias_declaration"],
            "tsx": ["function_declaration", "class_declaration", "method_definition", "interface_declaration", "type_alias_declaration"],
            "go": ["function_declaration", "method_declaration", "type_declaration"],
            "java": ["class_declaration", "method_declaration"],
            "rust": ["function_item", "struct_item", "enum_item", "impl_item", "trait_item"],
        }
        
        current_lang_targets = target_types.get(lang_name, [])
        
        if node.type in current_lang_targets:
            chunk_text = code[node.start_byte:node.end_byte]
            chunks.append(chunk_text)
            return True # Found a chunk, don't recurse deeper for now
        
        # If not a target, check children
        for child in node.children:
            collect_chunks(child)
        return False

    collect_chunks(tree.root_node)
    
    # Post-process: If no chunks were found (e.g. script with only top-level statements),
    # or if some code is outside of blocks, this should be caught by the fallback anyway.
    # We return the collected semantic chunks.
    return chunks
