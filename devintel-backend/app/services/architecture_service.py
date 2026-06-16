"""Architecture visualization service for generating diagrams."""

from typing import Any, Optional
from uuid import UUID

from app.core.logging import get_logger
from app.integrations.openai_client import OpenAIClient
from app.models.architecture import ArchitectureDiagram, DiagramType
from app.models.repository import Repository
from app.repositories.architecture import ArchitectureDiagramRepository
from app.services.code_structure_analyzer import CodeStructureAnalyzer

logger = get_logger(__name__)


class ArchitectureVisualizationService:
    """Generate architecture diagrams from codebase analysis."""

    def __init__(self, db_session):
        self.db = db_session
        self.openai_client = OpenAIClient()

    async def generate_mermaid_diagram(
        self,
        repository: Repository,
        diagram_type: str = "mermaid",
        focus_paths: Optional[list[str]] = None,
    ) -> ArchitectureDiagram:
        """
        Generate a Mermaid architecture diagram from repository code.

        Args:
            repository: Repository to analyze
            diagram_type: Type of diagram (mermaid, c4_context, etc.)
            focus_paths: Optional list of paths to focus on

        Returns:
            ArchitectureDiagram model instance
        """
        # Analyze code structure
        analyzer = CodeStructureAnalyzer()
        structure = await analyzer.analyze_repository(
            repository=repository,
            focus_paths=focus_paths,
        )

        # Build Mermaid diagram based on analysis
        mermaid_code = self._generate_mermaid_from_structure(structure, diagram_type)

        # Create diagram record
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
        if diagram_type == DiagramType.MERMAID:
            return self._generate_flowchart(structure)
        elif diagram_type == DiagramType.C4_CONTEXT:
            return self._generate_c4_context(structure)
        elif diagram_type == DiagramType.C4_CONTAINER:
            return self._generate_c4_container(structure)
        else:
            return self._generate_flowchart(structure)

    def _generate_flowchart(self, structure: dict[str, Any]) -> str:
        """Generate Mermaid flowchart from structure."""
        lines = ["graph TD"]

        # Add nodes for each file/component
        for node_id, node in structure.get("nodes", {}).items():
            shape = "[]", "((", ">{", "([", "{{"  # rectangle, circle, rounded, stadium, subroutine
            shape_type = node.get("type", "function")
            if shape_type == "class":
                lines.append(f"    {node_id}[\"{node['name']}\"]")
            elif shape_type == "module":
                lines.append(f"    {node_id}(\"{node['name']}\")")
            else:
                lines.append(f"    {node_id}[\"{node['name']}\"]")

        # Add edges
        for edge in structure.get("edges", []):
            lines.append(f"    {edge['from']} --> {edge['to']}")

        return "\n".join(lines)

    def _generate_c4_context(self, structure: dict[str, Any]) -> str:
        """Generate C4 context diagram."""
        lines = [
            "C4Context",
            "    title System Context diagram for DevIntel AI",
            "",
            "    Person(user, \"User\", \"Developer using DevIntel AI\")",
            "    System(devintel, \"DevIntel AI\", \"Autonomous code intelligence platform\")",
            "",
        ]

        for dep in structure.get("external_deps", []):
            lines.append(f"    System_Ext({dep['id']}, \"{dep['name']}\", \"{dep.get('desc', '')}\")")

        lines.append("")
        lines.append("    Rel(user, devintel, \"Uses\")")
        for dep in structure.get("external_deps", []):
            lines.append(f"    Rel(devintel, {dep['id']}, \"Integrates with\")")

        lines.append("    UpdateLayoutConfig($c4ShapeInStyle, $c4BoundaryInStyle)")

        return "\n".join(lines)

    def _generate_c4_container(self, structure: dict[str, Any]) -> str:
        """Generate C4 container diagram."""
        lines = [
            "C4Container",
            "    title Container diagram for DevIntel AI",
            "",
            "    Container(api, \"API Service\", \"FastAPI\", \"REST API endpoints\")",
            "    Container(db, \"Database\", \"PostgreSQL + pgvector\", \"Vector embeddings and metadata\")",
            "    Container(web, \"Frontend\", \"React/TypeScript\", \"Web interface\")",
            "    Container(worker, \"Worker\", \"Python\", \"Async indexing jobs\")",
            "",
        ]

        for module in structure.get("modules", []):
            lines.append(f"    Component({module['id']}, \"{module['name']}\", \"{module.get('tech', 'Python')}\")")

        lines.append("")
        lines.append("    Rel(api, db, \"Reads/writes\")")
        lines.append("    Rel(web, api, \"Calls API\")")
        lines.append("    Rel_L(worker, api, \"Enqueues jobs\")")

        return "\n".join(lines)


class CodeStructureAnalyzer:
    """Analyze codebase structure for diagram generation."""

    async def analyze_repository(
        self,
        repository: Repository,
        focus_paths: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Analyze repository code structure.

        Returns dict with nodes, edges, modules, and dependencies.
        """
        # This would integrate with Tree-Sitter for AST analysis
        # For now, return a basic structure
        return {
            "nodes": {
                "api": {"name": "API Router", "type": "module"},
                "models": {"name": "Models", "type": "module"},
                "services": {"name": "Services", "type": "module"},
            },
            "edges": [
                {"from": "api", "to": "services"},
                {"from": "services", "to": "models"},
            ],
            "modules": [
                {"id": "chat_module", "name": "Chat Module", "tech": "FastAPI"},
                {"id": "rag_module", "name": "RAG Module", "tech": "OpenAI"},
            ],
            "external_deps": [
                {"id": "github", "name": "GitHub API", "desc": "Source control integration"},
                {"id": "openai", "name": "OpenAI API", "desc": "LLM and embeddings"},
            ],
        }