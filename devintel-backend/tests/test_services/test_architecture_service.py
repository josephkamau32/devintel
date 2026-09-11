"""Tests for architecture_service.CodeStructureAnalyzer.

Validates that real AST-based analysis produces correct, non-stub
output and that capping / edge-case logic works.
"""

import pytest

from app.services.architecture_service import CodeStructureAnalyzer, _path_to_module, _import_to_module


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
