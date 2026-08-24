# Import all models here so Alembic can detect them
from app.models.analytics import Analytics
from app.models.architecture import ArchitectureDiagram
from app.models.base import Base
from app.models.chat import Chat
from app.models.code_chunk import CodeChunk
from app.models.code_graph import CodeGraph
from app.models.code_health import CodeHealth
from app.models.collaboration import CollaborationMessage, CollaborationSession
from app.models.cross_repo import CrossRepoKnowledge
from app.models.embedding import Embedding
from app.models.generated_test import GeneratedTest
from app.models.git_history import FileBlame, GitHistory
from app.models.indexing_job import IndexingJob
from app.models.migration import MigratedFile, MigrationProject
from app.models.organization import Organization, OrganizationMember
from app.models.policy import Policy
from app.models.repository import Repository
from app.models.user import User

__all__ = [
    "Base", "User", "Repository", "CodeChunk",
    "Organization", "OrganizationMember", "Chat", "Analytics",
    "Policy", "GeneratedTest", "CodeGraph", "Embedding",
    "CollaborationSession", "CollaborationMessage",
    "CrossRepoKnowledge", "GitHistory", "FileBlame",
    "MigrationProject", "MigratedFile", "CodeHealth",
    "ArchitectureDiagram", "IndexingJob"
]
