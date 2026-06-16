"""Call graph extraction using Tree-Sitter."""

import os
from typing import Optional

import tree_sitter_language_pack as tslp
from tree_sitter import Language, Parser


def get_language_for_extension(ext: str) -> Optional[str]:
    """Map file extension to tree-sitter language."""
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


def extract_call_graph(code: str, file_path: str) -> list[tuple[str, str, str]]:
    """
    Extract function call relationships from code.

    Returns:
        List of (caller_name, callee_name, call_type) tuples
    """
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

    calls = []

    def extract_calls(node, caller_stack=None):
        """Recursively extract function calls from AST."""
        if caller_stack is None:
            caller_stack = []

        # Detect function/class definitions as callers
        if node.type in ("function_definition", "function_declaration", "method_definition",
                         "function_item", "method_item"):
            name_node = node.child(1) if len(node.children) > 1 else None
            if name_node:
                caller_stack.append(name_node.text.decode("utf8"))

        # Detect call expressions
        if node.type in ("call", "call_expression"):
            # Extract callee name
            for child in node.children:
                if child.type == "identifier":
                    callee = child.text.decode("utf8")
                    caller = caller_stack[-1] if caller_stack else "module"
                    calls.append((caller, callee, "direct_call"))
                    break
                elif child.type == "member":
                    # Method call like obj.method()
                    callee = child.text.decode("utf8")
                    caller = caller_stack[-1] if caller_stack else "module"
                    calls.append((caller, callee, "method_call"))
                    break

        for child in node.children:
            extract_calls(child, caller_stack.copy())

    def walk(node):
        """Walk the tree and extract calls."""
        extract_calls(node)
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return calls


def extract_calls_from_directory(repo_path: str) -> list[tuple[str, str, str]]:
    """
    Extract call graph from all supported files in a repository.

    Returns:
        List of (file_path, caller, callee, call_type) tuples
    """
    all_calls = []

    for root, _, files in os.walk(repo_path):
        # Skip ignored directories
        skip = False
        for ignored in ["node_modules", ".git", "dist", "build", "__pycache__"]:
            if ignored in root:
                skip = True
                break
        if skip:
            continue

        for file in files:
            file_path = os.path.join(root, file)
            ext = file.split('.')[-1].lower() if '.' in file else ""
            if ext not in get_language_for_extension(ext) and ext not in ["py", "js", "ts", "tsx", "jsx", "go", "java", "rs", "rb"]:
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                calls = extract_call_graph(content, file_path)
                rel_path = os.path.relpath(file_path, repo_path)
                for caller, callee, call_type in calls:
                    all_calls.append((rel_path, caller, callee, call_type))
            except Exception:
                pass

    return all_calls