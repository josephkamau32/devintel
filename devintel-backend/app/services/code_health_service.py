"""Code Health Service — LLM-powered per-repository quality analysis."""

import json
from typing import Any, Dict, List
from uuid import UUID

from app.core.logging import get_logger
from app.integrations.openai_client import OpenAIClient
from app.models.repository import Repository
from app.repositories.code_health import CodeHealthRepository
from app.repositories.embedding import EmbeddingRepository
from app.services.embedding import EmbeddingService

logger = get_logger(__name__)

# Probe queries used to sample diverse sections of the codebase.
# These hit different semantic regions: structure, logic, safety, docs.
PROBE_QUERIES = [
    "class definition and constructor",
    "function implementation business logic",
    "error handling exception",
    "TODO FIXME hack workaround",
    "unit test assert mock",
    "documentation docstring comment",
    "authentication authorization security",
    "database query SQL model",
    "API endpoint route handler",
    "configuration environment variable",
]


class CodeHealthService:
    """Analyzes a repository's code quality using RAG sampling + GPT-4."""

    def __init__(self) -> None:
        self.openai_client = OpenAIClient()
        self.embedding_service = EmbeddingService()

    async def analyze(
        self,
        repository: Repository,
        embedding_repo: EmbeddingRepository,
        health_repo: CodeHealthRepository,
    ) -> Dict[str, Any]:
        """
        Run a full code health analysis and persist the results.

        Steps:
        1. Sample representative code chunks via probe queries
        2. Deduplicate and build a compact context snapshot
        3. Call OpenAI for structured JSON scoring
        4. Upsert result into the code_health table

        Returns:
            The upserted health record as a dict.
        """
        repo_name = repository.full_name
        logger.info(f"Starting code health analysis for {repo_name}")

        # 1. Sample chunks from diverse codebase areas
        sampled_chunks = await self._sample_chunks(
            repo_id=repository.id,
            embedding_repo=embedding_repo,
            top_k_per_query=2,
        )

        if not sampled_chunks:
            logger.warning(f"No chunks found for health analysis of {repo_name}")
            return await self._persist_empty_result(repository.id, health_repo)

        # 2. Build context text (compact)
        context_text = self._build_context(sampled_chunks, max_chars=12000)

        # 3. Determine dominant language
        language = repository.language or "Unknown"

        # 4. Call OpenAI
        analysis = await self._call_llm(repo_name, language, context_text, len(sampled_chunks))

        # 5. Persist
        record = await health_repo.upsert(
            repo_id=repository.id,
            data={
                "overall_score": analysis.get("overall_score", 0.0),
                "complexity_score": analysis.get("complexity_score", 0.0),
                "documentation_score": analysis.get("documentation_score", 0.0),
                "maintainability_score": analysis.get("maintainability_score", 0.0),
                "test_coverage_score": analysis.get("test_coverage_score", 0.0),
                "security_score": analysis.get("security_score", 0.0),
                "summary": analysis.get("summary", ""),
                "top_issues": json.dumps(analysis.get("top_issues", [])),
                "recommendations": json.dumps(analysis.get("recommendations", [])),
                "language_detected": language,
                "files_analyzed": len(sampled_chunks),
            },
        )

        logger.info(
            f"Code health for {repo_name}: overall={analysis.get('overall_score', 0):.1f}/100"
        )
        return self._record_to_dict(record)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _sample_chunks(
        self,
        repo_id: UUID,
        embedding_repo: EmbeddingRepository,
        top_k_per_query: int = 2,
    ) -> List[Any]:
        """Run all probe queries in parallel and deduplicate results."""
        import asyncio

        seen_ids: set = set()
        results: list = []

        async def _run_probe(query: str):
            try:
                emb = await self.embedding_service.generate_embedding(query)
                hits = await embedding_repo.vector_search(
                    repo_id=repo_id,
                    query_embedding=emb,
                    top_k=top_k_per_query,
                )
                return hits
            except Exception as exc:
                logger.warning(f"Probe '{query}' failed: {exc}")
                return []

        all_hits = await asyncio.gather(*[_run_probe(q) for q in PROBE_QUERIES])

        for hit_list in all_hits:
            for emb, _sim in hit_list:
                if emb.id not in seen_ids:
                    seen_ids.add(emb.id)
                    results.append(emb)

        return results

    def _build_context(self, chunks: list, max_chars: int = 12000) -> str:
        """Build a compact context string from sampled chunks."""
        parts, total_chars = [], 0
        for chunk in chunks:
            snippet = f"\n--- {chunk.file_path} ---\n{chunk.chunk_text[:400]}"
            if total_chars + len(snippet) > max_chars:
                break
            parts.append(snippet)
            total_chars += len(snippet)
        return "\n".join(parts)

    async def _call_llm(
        self,
        repo_name: str,
        language: str,
        context_text: str,
        files_analyzed: int,
    ) -> Dict[str, Any]:
        """Call the OpenAI API for a structured code quality assessment."""
        system_prompt = f"""You are an expert software quality engineer analyzing repository: {repo_name}.
Primary language: {language}
Files sampled: {files_analyzed}

Codebase samples:
{context_text}

Analyze the code quality across these 6 dimensions and respond with ONLY valid JSON:
{{
  "overall_score": <0-100 float>,
  "complexity_score": <0-100 float, higher = less complex / better>,
  "documentation_score": <0-100 float>,
  "maintainability_score": <0-100 float>,
  "test_coverage_score": <0-100 float>,
  "security_score": <0-100 float>,
  "summary": "<2-3 sentence executive summary of code quality>",
  "top_issues": ["<issue 1>", "<issue 2>", "<issue 3>"],
  "recommendations": ["<actionable rec 1>", "<actionable rec 2>", "<actionable rec 3>"]
}}

Be objective, use the sampled code as evidence. Score 0=very poor, 50=average, 100=excellent."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze code health for {repo_name}"},
        ]

        try:
            response = await self.openai_client.chat_completion(
                messages=messages,
                temperature=0.05,
                max_tokens=800,
            )
            raw = response.content if hasattr(response, "content") else str(response)
            return self._parse_json(raw)
        except Exception as e:
            logger.error(f"LLM call failed for code health analysis: {e}")
            return self._default_result()

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with fallback."""
        content = raw.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start, end = content.find("{"), content.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass
        return self._default_result()

    def _default_result(self) -> Dict[str, Any]:
        return {
            "overall_score": 50.0,
            "complexity_score": 50.0,
            "documentation_score": 50.0,
            "maintainability_score": 50.0,
            "test_coverage_score": 50.0,
            "security_score": 50.0,
            "summary": "Analysis could not be completed. Scores are indicative defaults.",
            "top_issues": [],
            "recommendations": [],
        }

    async def _persist_empty_result(
        self,
        repo_id: UUID,
        health_repo: CodeHealthRepository,
    ) -> Dict[str, Any]:
        """Persist a default result when no chunks are available."""
        result = self._default_result()
        record = await health_repo.upsert(
            repo_id=repo_id,
            data={**result, "files_analyzed": 0, "language_detected": None,
                  "top_issues": json.dumps([]), "recommendations": json.dumps([])},
        )
        return self._record_to_dict(record)

    @staticmethod
    def _record_to_dict(record) -> Dict[str, Any]:
        return {
            "id": str(record.id),
            "repo_id": str(record.repo_id),
            "overall_score": record.overall_score,
            "complexity_score": record.complexity_score,
            "documentation_score": record.documentation_score,
            "maintainability_score": record.maintainability_score,
            "test_coverage_score": record.test_coverage_score,
            "security_score": record.security_score,
            "summary": record.summary,
            "top_issues": json.loads(record.top_issues or "[]"),
            "recommendations": json.loads(record.recommendations or "[]"),
            "language_detected": record.language_detected,
            "files_analyzed": record.files_analyzed,
            "computed_at": record.computed_at.isoformat() if record.computed_at else None,
        }
