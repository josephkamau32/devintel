"""Prompt registry — loads versioned prompt templates from YAML files.

Templates use Python string.Template-style ``$variable`` placeholders
which are substituted at render time.  Every template file must contain:

- ``name``: unique identifier (e.g. ``pr_review``)
- ``version``: semver string (e.g. ``1.0.0``)
- ``description``: human-readable description
- ``messages``: list of ``{role, content}`` dicts (the actual prompt)

Optional fields:
- ``model``: default model override for this prompt
- ``temperature``: default temperature
- ``max_tokens``: default max_tokens
- ``tags``: list of categorization tags
"""

from __future__ import annotations

import os
from pathlib import Path
from string import Template
from typing import Any, Optional

import yaml

from app.core.logging import get_logger

logger = get_logger(__name__)

# Directory containing YAML prompt templates
_PROMPTS_DIR = Path(__file__).parent / "templates"


class PromptTemplate:
    """A loaded, renderable prompt template."""

    def __init__(self, data: dict[str, Any], file_path: str = "") -> None:
        self.name: str = data["name"]
        self.version: str = data.get("version", "1.0.0")
        self.description: str = data.get("description", "")
        self.messages_raw: list[dict[str, str]] = data["messages"]
        self.model: Optional[str] = data.get("model")
        self.temperature: Optional[float] = data.get("temperature")
        self.max_tokens: Optional[int] = data.get("max_tokens")
        self.tags: list[str] = data.get("tags", [])
        self._file_path = file_path

    def render(self, **kwargs: str) -> list[dict[str, str]]:
        """Render messages by substituting ``$variable`` placeholders.

        Args:
            **kwargs: Template variables to substitute.

        Returns:
            List of ``{role, content}`` dicts ready for the orchestrator.
        """
        rendered = []
        for msg in self.messages_raw:
            content = Template(msg["content"]).safe_substitute(**kwargs)
            rendered.append({"role": msg["role"], "content": content})
        return rendered

    def __repr__(self) -> str:
        return f"PromptTemplate(name={self.name!r}, version={self.version!r})"


class PromptRegistry:
    """In-memory registry of all YAML prompt templates.

    Templates are loaded from ``app/ai/prompts/templates/*.yaml`` at
    initialization time and can be retrieved by name.
    """

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Scan the templates directory and load all .yaml files."""
        if not _PROMPTS_DIR.exists():
            logger.warning("Prompts directory not found: %s", _PROMPTS_DIR)
            return

        for yaml_file in sorted(_PROMPTS_DIR.glob("*.yaml")):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not data or "name" not in data or "messages" not in data:
                    logger.warning("Skipping invalid prompt file: %s", yaml_file.name)
                    continue

                template = PromptTemplate(data, file_path=str(yaml_file))
                self._templates[template.name] = template
                logger.debug("Loaded prompt template: %s v%s", template.name, template.version)

            except Exception as e:
                logger.error("Failed to load prompt file %s: %s", yaml_file.name, e)

        logger.info("Loaded %d prompt templates", len(self._templates))

    def get(self, name: str) -> PromptTemplate:
        """Retrieve a template by name.

        Raises:
            KeyError: If no template with that name exists.
        """
        if name not in self._templates:
            available = ", ".join(sorted(self._templates.keys())) or "(none)"
            raise KeyError(
                f"Prompt template '{name}' not found. Available: {available}"
            )
        return self._templates[name]

    def list_templates(self) -> list[dict[str, str]]:
        """Return metadata for all loaded templates."""
        return [
            {
                "name": t.name,
                "version": t.version,
                "description": t.description,
                "tags": t.tags,
            }
            for t in sorted(self._templates.values(), key=lambda t: t.name)
        ]

    def reload(self) -> None:
        """Hot-reload all templates from disk."""
        self._templates.clear()
        self._load_all()

    def __contains__(self, name: str) -> bool:
        return name in self._templates

    def __len__(self) -> int:
        return len(self._templates)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_registry: Optional[PromptRegistry] = None


def get_prompt_registry() -> PromptRegistry:
    """Return the global PromptRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry
