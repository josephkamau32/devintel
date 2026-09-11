"""Architecture visualization service for generating diagrams.

Replaces the former hardcoded stub with real AST-based analysis
using the existing symbol_graph module and stored embedding chunks.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.architecture import ArchitectureDiagram, DiagramType
from app.models.embedding import Embedding
from app.models.repository import Repository
from app.repositories.architecture import ArchitectureDiagramRepository

logger = get_logger(__name__)

# --- Caps for readable diagrams ---
MAX_MODULE_NODES = 20
MAX_EDGES = 50


class ArchitectureVisualizationService:
    """Generate architecture diagrams from codebase analysis."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def generate_mermaid_diagram(
        self,
        repository: Repository,
        diagram_type: str = "mermaid",
        focus_paths: Optional[list[str]] = None,
    ) -> ArchitectureDiagram:
        """
        Generate a Mermaid architecture diagram from repository code.

        Uses stored embedding chunks as the source of truth for the
        repository's code — this is the production code path.
        """
        analyzer = CodeStructureAnalyzer()
        structure = await analyzer.from_embeddings(
            repo_id=repository.id,
            session=self.db,
        )

        mermaid_code = self._generate_mermaid_from_structure(structure, diagram_type)

        diagram_repo = ArchitectureDiagramRepository(self.db)
        diagram = await diagram_repo.create(
            repo_id=repository.id,
            name=f"{repository.repo_name} Architecture",
            diagram_type=diagram_type,
            mermaid_code=mermaid_code,
        )
        await self.db.commit()

        return diagram

    def _generate_mermaid_from_structure(
        self,
        structure: dict[str, Any],
        diagram_type: str,
    ) -> str:
        """Generate Mermaid code from code structure."""
        if diagram_type == DiagramType.C4_CONTEXT:
            return self._generate_c4_context(structure)
        elif diagram_type == DiagramType.C4_CONTAINER:
            return self._generate_c4_container(structure)
        else:
            return self._generate_flowchart(structure)

    def _generate_flowchart(self, structure: dict[str, Any]) -> str:
        """Generate Mermaid flowchart with subgraph module grouping."""
        lines = ["graph TD"]

        modules = structure.get("modules", {})
        edges = structure.get("edges", [])
        capping_note = structure.get("capping_note", "")

        if not modules:
            lines.append('    empty["No parseable code structure found"]')
            return "\n".join(lines)

        # Emit subgraphs per module
        for mod_id, mod_info in modules.items():
            label = mod_info["label"]
            classes = mod_info.get("classes", [])
            functions = mod_info.get("top_functions", [])
            class_count = mod_info.get("class_count", 0)
            func_count = mod_info.get("function_count", 0)

            safe_id = _safe_mermaid_id(mod_id)
            lines.append(f"    subgraph {safe_id}[\"{label}\"]")

            # Show up to 6 classes and 4 top-level functions per module
            shown_items = 0
            for cls_name in classes[:6]:
                item_id = _safe_mermaid_id(f"{mod_id}__{cls_name}")
                lines.append(f'        {item_id}["{cls_name}"]')
                shown_items += 1
            for fn_name in functions[:4]:
                item_id = _safe_mermaid_id(f"{mod_id}__{fn_name}")
                lines.append(f'        {item_id}("{fn_name}()")')
                shown_items += 1

            # If no individual items, show a summary node
            if shown_items == 0:
                summary_id = _safe_mermaid_id(f"{mod_id}__summary")
                lines.append(
                    f'        {summary_id}["{class_count} classes, {func_count} functions"]'
                )

            lines.append("    end")

        # Emit edges between modules
        for edge in edges:
            from_id = _safe_mermaid_id(edge["from"])
            to_id = _safe_mermaid_id(edge["to"])
            count = edge.get("count", 1)
            if count > 1:
                lines.append(f"    {from_id} -->|{count} imports| {to_id}")
            else:
                lines.append(f"    {from_id} --> {to_id}")

        # Honest capping note
        if capping_note:
            note_id = _safe_mermaid_id("capping_note")
            lines.append(f'    {note_id}[/"{capping_note}"/]')
            lines.append(f"    style {note_id} fill:#553,stroke:#aa0,color:#ff0")

        return "\n".join(lines)

    def _generate_c4_context(self, structure: dict[str, Any]) -> str:
        """Generate C4 context diagram."""
        lines = [
            "C4Context",
            '    title System Context diagram',
            "",
            '    Person(user, "User", "Developer")',
            '    System(app, "Application", "Analyzed codebase")',
            "",
        ]

        for dep in structure.get("external_deps", []):
            lines.append(
                f'    System_Ext({dep["id"]}, "{dep["name"]}", "{dep.get("desc", "")}")'
            )

        lines.append("")
        lines.append('    Rel(user, app, "Uses")')
        for dep in structure.get("external_deps", []):
            lines.append(f'    Rel(app, {dep["id"]}, "Integrates with")')

        return "\n".join(lines)

    def _generate_c4_container(self, structure: dict[str, Any]) -> str:
        """Generate C4 container diagram."""
        lines = [
            "C4Container",
            '    title Container diagram',
            "",
        ]

        for mod_id, mod_info in structure.get("modules", {}).items():
            safe_id = _safe_mermaid_id(mod_id)
            lines.append(
                f'    Container({safe_id}, "{mod_info["label"]}", "Python")'
            )

        return "\n".join(lines)


class CodeStructureAnalyzer:
    """Analyze codebase structure for diagram generation.

    The primary production method is ``from_embeddings()`` which
    reconstructs source files from stored embedding chunks and then
    runs real AST analysis via ``symbol_graph.build_symbol_graph()``.
    """

    # ------------------------------------------------------------------
    # Production path: reconstruct files from stored chunks
    # ------------------------------------------------------------------

    async def from_embeddings(
        self,
        repo_id: UUID,
        session: AsyncSession,
    ) -> dict[str, Any]:
        """Build a real architecture graph from a repo's stored embedding chunks.

        Chunk reconstruction logic:
        1. Query ALL embeddings for ``repo_id``, ordered by
           (file_path ASC, chunk_index ASC).
        2. Group rows by ``file_path``.
        3. For each file, sort chunks by ``chunk_index`` (ascending)
           and concatenate their ``chunk_text`` fields — this
           reconstitutes the file content in the order it was
           originally chunked.
        4. If chunk_index values have gaps (e.g. 0, 1, 3 — missing 2)
           we still concatenate what we have but flag the file as
           incomplete in the logs. The resulting AST parse may be
           partial but will not crash (tree-sitter is tolerant).
        """
        result = await session.execute(
            select(
                Embedding.file_path,
                Embedding.chunk_index,
                Embedding.chunk_text,
            )
            .where(Embedding.repo_id == repo_id)
            .order_by(Embedding.file_path, Embedding.chunk_index)
        )
        rows = result.fetchall()

        if not rows:
            logger.warning("No embedding chunks found for repo %s", repo_id)
            return {"modules": {}, "edges": [], "external_deps": []}

        # Group chunks by file_path, maintaining chunk_index order
        file_chunks: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for file_path, chunk_index, chunk_text in rows:
            file_chunks[file_path].append((chunk_index, chunk_text))

        # Reconstruct files
        files: dict[str, str] = {}
        incomplete_files: list[str] = []

        for file_path, chunks in file_chunks.items():
            # Sort by chunk_index (should already be sorted by DB query, but be safe)
            chunks.sort(key=lambda c: c[0])

            # Check for gaps in chunk_index
            indices = [c[0] for c in chunks]
            expected = list(range(indices[0], indices[-1] + 1))
            if indices != expected:
                incomplete_files.append(file_path)
                logger.warning(
                    "File %s has chunk index gaps: expected %s, got %s",
                    file_path, expected, indices,
                )

            # Concatenate chunk texts in order
            files[file_path] = "".join(text for _, text in chunks)

        if incomplete_files:
            logger.warning(
                "%d files had incomplete chunks: %s",
                len(incomplete_files),
                incomplete_files[:5],
            )

        logger.info(
            "Reconstructed %d files from %d chunks for repo %s",
            len(files), len(rows), repo_id,
        )

        return self._analyze_files(files)

    # ------------------------------------------------------------------
    # Direct-files path (for tests and seed script only)
    # ------------------------------------------------------------------

    def from_files(self, files: dict[str, str]) -> dict[str, Any]:
        """Build architecture graph directly from a dict of {path: code}.

        This is a convenience method for tests and the seed script.
        The production API always uses ``from_embeddings()``.
        """
        return self._analyze_files(files)

    # ------------------------------------------------------------------
    # Core analysis logic (shared by both paths)
    # ------------------------------------------------------------------

    def _analyze_files(self, files: dict[str, str]) -> dict[str, Any]:
        """Parse files via tree-sitter and build the module graph."""
        from app.utils.symbol_graph import build_symbol_graph

        graph = build_symbol_graph(files, include_calls=False)

        # Build module-level groupings
        # A "module" = the first two path segments (e.g. "app/services")
        module_symbols: dict[str, dict] = defaultdict(
            lambda: {"classes": [], "functions": [], "files": set()}
        )

        for sym in graph.symbols:
            mod = _path_to_module(sym.file_path)
            module_symbols[mod]["files"].add(sym.file_path)
            if sym.kind == "class":
                module_symbols[mod]["classes"].append(sym.name)
            elif sym.kind == "function":
                module_symbols[mod]["functions"].append(sym.name)

        # Build import edges between modules
        edge_counter: dict[tuple[str, str], int] = defaultdict(int)
        for imp in graph.imports:
            src_mod = _path_to_module(imp.file_path)
            tgt_mod = _import_to_module(imp.module)

            # Only keep edges where both modules are in our codebase
            if tgt_mod and tgt_mod in module_symbols and tgt_mod != src_mod:
                edge_counter[(src_mod, tgt_mod)] += 1

        # Apply capping
        capping_note = ""
        all_mods = dict(module_symbols)

        if len(all_mods) > MAX_MODULE_NODES:
            original_count = len(all_mods)
            # Keep the modules with the most files/symbols
            sorted_mods = sorted(
                all_mods.keys(),
                key=lambda m: len(all_mods[m]["classes"]) + len(all_mods[m]["functions"]),
                reverse=True,
            )
            kept = set(sorted_mods[:MAX_MODULE_NODES])
            all_mods = {k: v for k, v in all_mods.items() if k in kept}
            capping_note = (
                f"Showing {MAX_MODULE_NODES} of {original_count} modules "
                f"(largest by symbol count)"
            )

        # Build edges list, cap if needed
        edges_list = [
            {"from": src, "to": tgt, "count": cnt}
            for (src, tgt), cnt in sorted(
                edge_counter.items(), key=lambda x: x[1], reverse=True
            )
            if src in all_mods and tgt in all_mods
        ]

        if len(edges_list) > MAX_EDGES:
            original_edge_count = len(edges_list)
            edges_list = edges_list[:MAX_EDGES]
            edge_note = (
                f"Showing {MAX_EDGES} of {original_edge_count} import relationships "
                f"(highest frequency)"
            )
            capping_note = f"{capping_note}; {edge_note}" if capping_note else edge_note

        # Build final modules dict
        modules_dict = {}
        for mod_id, info in all_mods.items():
            modules_dict[mod_id] = {
                "label": mod_id.replace("/", "."),
                "classes": sorted(set(info["classes"])),
                "top_functions": sorted(set(info["functions"]))[:6],
                "class_count": len(set(info["classes"])),
                "function_count": len(set(info["functions"])),
                "file_count": len(info["files"]),
            }

        # Detect external dependencies from imports
        external_deps = _detect_external_deps(graph.imports, module_symbols)

        return {
            "modules": modules_dict,
            "edges": edges_list,
            "external_deps": external_deps,
            "capping_note": capping_note,
            "stats": {
                "total_files": len(set(s.file_path for s in graph.symbols)),
                "total_classes": len(graph.get_classes()),
                "total_functions": len(graph.get_functions()),
                "total_imports": len(graph.imports),
            },
        }


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------

def _safe_mermaid_id(s: str) -> str:
    """Convert a path/name to a valid Mermaid node ID."""
    return s.replace("/", "_").replace(".", "_").replace("-", "_").replace(" ", "_")


def _path_to_module(file_path: str) -> str:
    """Extract the module (first 2 path segments) from a file path.

    Examples:
        "app/services/auth.py"  → "app/services"
        "app/ai/providers/x.py" → "app/ai"
        "utils.py"              → "root"
    """
    parts = file_path.replace("\\", "/").split("/")
    # Remove the filename
    dir_parts = parts[:-1]
    if len(dir_parts) >= 2:
        return "/".join(dir_parts[:2])
    elif len(dir_parts) == 1:
        return dir_parts[0]
    else:
        return "root"


def _import_to_module(import_module: str) -> str | None:
    """Convert an import module string to a module path.

    Examples:
        "app.services.auth_service" → "app/services"
        "app.ai.orchestrator"       → "app/ai"
        "sqlalchemy"                → None (external)
    """
    parts = import_module.split(".")
    if len(parts) >= 2 and parts[0] in ("app",):
        return "/".join(parts[:2])
    return None


def _detect_external_deps(
    imports: list, module_symbols: dict
) -> list[dict[str, str]]:
    """Detect external (non-app) dependencies from imports."""
    external = set()
    for imp in imports:
        top = imp.module.split(".")[0]
        if top and top not in ("app",) and not top.startswith("_"):
            external.add(top)

    known_desc = {
        "sqlalchemy": "SQL ORM",
        "fastapi": "Web Framework",
        "pydantic": "Data Validation",
        "google": "Google AI SDK",
        "openai": "OpenAI SDK",
        "github": "GitHub API",
        "httpx": "HTTP Client",
        "jwt": "JWT Auth",
        "passlib": "Password Hashing",
        "tiktoken": "Tokenizer",
        "tree_sitter": "AST Parser",
    }

    return [
        {
            "id": _safe_mermaid_id(dep),
            "name": dep,
            "desc": known_desc.get(dep, "External library"),
        }
        for dep in sorted(external)[:10]  # Cap at 10 external deps
    ]
