"""Tests for architecture_service.CodeStructureAnalyzer.

Validates that real AST-based analysis produces correct, non-stub
output and that capping / edge-case logic works.
"""

import re

import pytest

from app.services.architecture_service import (
    ArchitectureVisualizationService,
    CodeStructureAnalyzer,
    MAX_LABEL_LENGTH,
    _escape_mermaid_label,
    _import_to_module,
    _path_to_module,
    _safe_mermaid_id,
)


# ---- Fixtures: two genuinely different file sets ----

FILESET_A = {
    "app/services/auth.py": '''
from app.models.user import User
from app.core.config import settings

class AuthService:
    """Handles user authentication."""
    async def login(self, username: str, password: str) -> User:
        pass

    async def register(self, email: str) -> User:
        pass
''',
    "app/models/user.py": '''
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()
''',
    "app/core/config.py": '''
class Settings:
    DEBUG: bool = False
    APP_NAME: str = "TestApp"

settings = Settings()
''',
}

FILESET_B = {
    "app/api/routes.py": '''
from fastapi import APIRouter
from app.services.payment import PaymentService

router = APIRouter()

def health_check():
    return {"status": "ok"}

def list_payments():
    svc = PaymentService()
    return svc.list()
''',
    "app/services/payment.py": '''
from app.models.transaction import Transaction

class PaymentService:
    def list(self):
        return []

    def process(self, amount: float):
        return Transaction(amount=amount)
''',
    "app/models/transaction.py": '''
class Transaction:
    def __init__(self, amount: float):
        self.amount = amount
''',
}


class TestCodeStructureAnalyzer:
    """Test the real CodeStructureAnalyzer (from_files path)."""

    def test_produces_real_modules_not_stub(self):
        """Output must reflect actual parsed code, not the old hardcoded stub."""
        analyzer = CodeStructureAnalyzer()
        result = analyzer.from_files(FILESET_A)

        modules = result["modules"]
        # Must NOT match the old stub keys
        assert "api" not in modules or modules.get("api", {}).get("label") != "API Router"
        assert "services" not in modules
        assert "models" not in modules

        # Must contain real modules derived from the file paths
        assert "app/services" in modules
        assert "app/models" in modules
        assert "app/core" in modules

    def test_two_different_filesets_produce_different_output(self):
        """Two genuinely different codebases must produce different graphs."""
        analyzer = CodeStructureAnalyzer()
        result_a = analyzer.from_files(FILESET_A)
        result_b = analyzer.from_files(FILESET_B)

        modules_a = set(result_a["modules"].keys())
        modules_b = set(result_b["modules"].keys())
        assert modules_a != modules_b, (
            f"Identical modules from different codebases — likely still stubbed. "
            f"A={modules_a}, B={modules_b}"
        )

    def test_classes_and_functions_extracted(self):
        """Real class and function names must appear in the output."""
        analyzer = CodeStructureAnalyzer()
        result = analyzer.from_files(FILESET_A)

        services_mod = result["modules"].get("app/services", {})
        assert "AuthService" in services_mod.get("classes", [])

        models_mod = result["modules"].get("app/models", {})
        assert "User" in models_mod.get("classes", [])

    def test_import_edges_reflect_real_imports(self):
        """Edges must be derived from real import statements."""
        analyzer = CodeStructureAnalyzer()
        result = analyzer.from_files(FILESET_A)

        edges = result["edges"]
        edge_pairs = {(e["from"], e["to"]) for e in edges}

        # auth.py imports from app.models and app.core
        assert ("app/services", "app/models") in edge_pairs
        assert ("app/services", "app/core") in edge_pairs

    def test_empty_files_produce_empty_diagram(self):
        """An empty file set should produce valid but empty output."""
        analyzer = CodeStructureAnalyzer()
        result = analyzer.from_files({})

        assert result["modules"] == {}
        assert result["edges"] == []

    def test_single_file_produces_output(self):
        """Even a single file should produce a valid graph."""
        analyzer = CodeStructureAnalyzer()
        result = analyzer.from_files({
            "app/main.py": "def main():\n    pass\n"
        })

        assert len(result["modules"]) >= 1

    def test_parse_error_does_not_crash(self):
        """Files with invalid syntax should be skipped gracefully."""
        analyzer = CodeStructureAnalyzer()
        result = analyzer.from_files({
            "app/broken.py": "def incomplete(",
            "app/good.py": "class Good:\n    pass\n",
        })

        # Should still produce results from the good file
        assert len(result["modules"]) >= 1

    def test_capping_limits_modules(self):
        """When more than MAX_MODULE_NODES modules exist, output is capped with a note."""
        # Generate 25 fake modules
        files = {}
        for i in range(25):
            files[f"pkg{i}/mod/file.py"] = f"class C{i}:\n    pass\n"

        analyzer = CodeStructureAnalyzer()
        result = analyzer.from_files(files)

        from app.services.architecture_service import MAX_MODULE_NODES
        assert len(result["modules"]) <= MAX_MODULE_NODES
        assert result["capping_note"], "Capping note must be present when modules are truncated"

    def test_no_capping_note_when_under_limit(self):
        """Small codebases should NOT have a capping note."""
        analyzer = CodeStructureAnalyzer()
        result = analyzer.from_files(FILESET_A)

        assert result.get("capping_note", "") == ""


class TestHelperFunctions:
    """Test the module/import path helpers."""

    def test_path_to_module(self):
        assert _path_to_module("app/services/auth.py") == "app/services"
        assert _path_to_module("app/ai/providers/gemini.py") == "app/ai"
        assert _path_to_module("utils.py") == "root"
        assert _path_to_module("app/main.py") == "app"

    def test_import_to_module(self):
        assert _import_to_module("app.services.auth") == "app/services"
        assert _import_to_module("app.ai.orchestrator") == "app/ai"
        assert _import_to_module("sqlalchemy") is None
        assert _import_to_module("fastapi") is None


class TestMermaidSanitization:
    """Verify hostile names cannot corrupt Mermaid output or inject markup."""

    @staticmethod
    def _assert_safe_mermaid_lines(mermaid: str) -> None:
        assert "<" not in mermaid
        assert "\\" not in mermaid
        for line in mermaid.splitlines():
            stripped = line.strip()
            if stripped.startswith("subgraph ") or '["' in stripped or '("' in stripped or '[/"' in stripped:
                assert ">" not in stripped
                assert stripped.count('"') == 2

    def test_hostile_directory_with_double_quote(self):
        analyzer = CodeStructureAnalyzer()
        svc = ArchitectureVisualizationService(None)  # type: ignore[arg-type]

        structure = analyzer.from_files({'a"b/mod.py': "class Foo:\n    pass\n"})
        mermaid = svc._generate_mermaid_from_structure(structure, "mermaid")

        assert mermaid.startswith("graph TD\n")
        assert '["a#quot;b"]' in mermaid
        self._assert_safe_mermaid_lines(mermaid)

        m = re.search(r"^\s*subgraph\s+([^\[\s]+)\[", mermaid, re.MULTILINE)
        assert m is not None
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", m.group(1))

    def test_hostile_directory_with_xss_markup(self):
        analyzer = CodeStructureAnalyzer()
        svc = ArchitectureVisualizationService(None)  # type: ignore[arg-type]

        structure = analyzer.from_files(
            {"<img src=x onerror=alert(1)>/evil.py": "def run():\n    pass\n"}
        )
        mermaid = svc._generate_mermaid_from_structure(structure, "mermaid")

        assert "<" not in mermaid
        assert ">" not in mermaid
        assert '["#lt;img src=x onerror=alert(1)#gt;"]' in mermaid
        self._assert_safe_mermaid_lines(mermaid)

        m = re.search(r"^\s*subgraph\s+([^\[\s]+)\[", mermaid, re.MULTILINE)
        assert m is not None
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", m.group(1))

    def test_very_long_directory_and_class_names(self):
        analyzer = CodeStructureAnalyzer()
        svc = ArchitectureVisualizationService(None)  # type: ignore[arg-type]

        long_dir = "very_long_" + ("x" * 250)
        long_cls = "VeryLongClass_" + ("Y" * 250)
        structure = analyzer.from_files({f"{long_dir}/mod.py": f"class {long_cls}:\n    pass\n"})
        mermaid = svc._generate_mermaid_from_structure(structure, "mermaid")

        self._assert_safe_mermaid_lines(mermaid)
        ids = re.findall(r"^\s*(?:subgraph\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\[", mermaid, re.MULTILINE)
        assert ids
        for node_id in ids:
            assert len(node_id) <= 80

        labels = re.findall(r'"([^"]*)"', mermaid)
        assert any(label.endswith("...") and len(label) <= MAX_LABEL_LENGTH for label in labels)

    def test_backslashes_and_newlines_escaped_across_diagram_types(self):
        svc = ArchitectureVisualizationService(None)  # type: ignore[arg-type]
        structure = {
            "modules": {
                'dir\\one"two': {
                    "label": 'dir\\one"two<script>\ninjected',
                    "classes": ['Cls\\A"B<C>'],
                    "top_functions": ['fn\\1"2<3>'],
                    "class_count": 1,
                    "function_count": 1,
                },
                "app/clean": {
                    "label": "app.clean",
                    "classes": ["Clean"],
                    "top_functions": [],
                    "class_count": 1,
                    "function_count": 0,
                },
            },
            "edges": [{"from": 'dir\\one"two', "to": "app/clean", "count": 2}],
            "external_deps": [
                {"id": 'evil"dep<1>', "name": 'evil\\"<pkg>', "desc": 'desc\\"<x>'}
            ],
            "capping_note": 'Note with \\ " and <tag>',
        }

        flowchart = svc._generate_mermaid_from_structure(structure, "mermaid")
        self._assert_safe_mermaid_lines(flowchart)
        assert "#92;" in flowchart
        assert "#quot;" in flowchart
        assert "#lt;" in flowchart
        assert "#gt;" in flowchart
        assert " -->|2 imports| app_clean" in flowchart

        subgraph_id = _safe_mermaid_id('dir\\one"two')
        assert f"subgraph {subgraph_id}[" in flowchart
        assert f"{subgraph_id} -->|2 imports| app_clean" in flowchart

        c4_ctx = svc._generate_mermaid_from_structure(structure, "c4_context")
        assert "<" not in c4_ctx and "\\" not in c4_ctx
        assert "#92;" in c4_ctx and "#quot;" in c4_ctx and "#lt;" in c4_ctx and "#gt;" in c4_ctx

        c4_cnt = svc._generate_mermaid_from_structure(structure, "c4_container")
        assert "<" not in c4_cnt and "\\" not in c4_cnt
        assert "#92;" in c4_cnt and "#quot;" in c4_cnt and "#lt;" in c4_cnt and "#gt;" in c4_cnt

    def test_escape_helper_does_not_split_entities_on_truncation(self):
        hostile = '"' * 120
        escaped = _escape_mermaid_label(hostile, max_len=10)
        # 10 chars truncated -> 7 quotes + "..." -> each quote is #quot;
        assert escaped == ("#quot;" * 7) + "..."
        assert '"' not in escaped
