"""Symbol graph — enriched code intelligence layer on top of call_graph.

Extracts classes, functions, imports, and their relationships from source
files using Tree-Sitter.  Provides the data model that powers:
- Architecture diagram generation
- Cross-file reference resolution
- Context-aware RAG retrieval
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from app.core.logging import get_logger
from app.utils.call_graph import get_language_for_extension

logger = get_logger(__name__)


@dataclass
class Symbol:
    """A code symbol (class, function, variable, import)."""

    name: str
    kind: str  # "class", "function", "method", "import", "variable"
    file_path: str
    line_start: int
    line_end: int
    parent: Optional[str] = None  # enclosing class/function name
    docstring: Optional[str] = None
    signature: Optional[str] = None


@dataclass
class ImportRef:
    """An import reference."""

    module: str
    name: Optional[str] = None  # specific imported name
    alias: Optional[str] = None
    file_path: str = ""
    line: int = 0


@dataclass
class SymbolGraph:
    """Complete symbol graph for a set of files."""

    symbols: list[Symbol] = field(default_factory=list)
    imports: list[ImportRef] = field(default_factory=list)
    calls: list[tuple[str, str, str]] = field(default_factory=list)

    def get_symbols_for_file(self, file_path: str) -> list[Symbol]:
        return [s for s in self.symbols if s.file_path == file_path]

    def get_classes(self) -> list[Symbol]:
        return [s for s in self.symbols if s.kind == "class"]

    def get_functions(self) -> list[Symbol]:
        return [s for s in self.symbols if s.kind in ("function", "method")]

    def find_symbol(self, name: str) -> Optional[Symbol]:
        for s in self.symbols:
            if s.name == name:
                return s
        return None

    def get_callers_of(self, name: str) -> list[str]:
        return [caller for caller, callee, _ in self.calls if callee == name]

    def get_callees_of(self, name: str) -> list[str]:
        return [callee for caller, callee, _ in self.calls if caller == name]


def extract_symbols(code: str, file_path: str) -> tuple[list[Symbol], list[ImportRef]]:
    """Extract symbols and imports from a source file using Tree-Sitter.

    Args:
        code: Source code content.
        file_path: File path for language detection.

    Returns:
        Tuple of (symbols, imports).
    """
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    lang_name = get_language_for_extension(ext)

    if not lang_name:
        return [], []

    try:
        import tree_sitter_language_pack as tslp
        from tree_sitter import Language, Parser

        language = Language(tslp.get_binding(lang_name))
        parser = Parser(language)
        tree = parser.parse(bytes(code, "utf8"))
    except Exception as e:
        logger.debug("Tree-sitter parse failed for %s: %s", file_path, e)
        return [], []

    symbols: list[Symbol] = []
    imports: list[ImportRef] = []

    def _walk(node, parent_name: Optional[str] = None):
        # Classes
        if node.type in ("class_definition", "class_declaration"):
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode("utf8") if name_node else "<anon>"
            symbols.append(Symbol(
                name=name,
                kind="class",
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                parent=parent_name,
            ))
            for child in node.children:
                _walk(child, parent_name=name)
            return

        # Functions/methods
        if node.type in ("function_definition", "function_declaration",
                         "method_definition", "arrow_function"):
            name_node = node.child_by_field_name("name")
            name = name_node.text.decode("utf8") if name_node else "<anon>"
            kind = "method" if parent_name else "function"

            # Try to extract signature
            params_node = node.child_by_field_name("parameters")
            sig = params_node.text.decode("utf8") if params_node else ""

            symbols.append(Symbol(
                name=name,
                kind=kind,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                parent=parent_name,
                signature=f"{name}({sig})" if sig else name,
            ))
            for child in node.children:
                _walk(child, parent_name=name)
            return

        # Python imports
        if node.type == "import_statement":
            text = node.text.decode("utf8")
            imports.append(ImportRef(
                module=text.replace("import ", "").strip(),
                file_path=file_path,
                line=node.start_point[0] + 1,
            ))

        if node.type == "import_from_statement":
            module_node = node.child_by_field_name("module_name")
            module = module_node.text.decode("utf8") if module_node else ""
            for child in node.children:
                if child.type == "dotted_name" and child != module_node:
                    imports.append(ImportRef(
                        module=module,
                        name=child.text.decode("utf8"),
                        file_path=file_path,
                        line=node.start_point[0] + 1,
                    ))

        # Recurse
        for child in node.children:
            _walk(child, parent_name)

    _walk(tree.root_node)
    return symbols, imports


def build_symbol_graph(
    files: dict[str, str],
    include_calls: bool = True,
) -> SymbolGraph:
    """Build a complete symbol graph from a dict of {file_path: code}.

    Args:
        files: Mapping of file paths to source code.
        include_calls: Whether to also extract call relationships.

    Returns:
        SymbolGraph with all symbols, imports, and calls.
    """
    from app.utils.call_graph import extract_call_graph

    graph = SymbolGraph()

    for file_path, code in files.items():
        symbols, imports = extract_symbols(code, file_path)
        graph.symbols.extend(symbols)
        graph.imports.extend(imports)

        if include_calls:
            calls = extract_call_graph(code, file_path)
            graph.calls.extend(calls)

    logger.info(
        "Symbol graph built: %d symbols, %d imports, %d calls across %d files",
        len(graph.symbols), len(graph.imports), len(graph.calls), len(files),
    )

    return graph
