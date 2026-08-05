"""Feature flags — centralized feature toggling for the platform.

Provides a simple, runtime-configurable flag system that supports:
- Environment variable overrides (``FEATURE_FLAG_<NAME>=true/false``)
- Default values defined in code
- Dynamic model routing for the AI orchestrator
- Flag introspection via API

Usage::

    from app.core.feature_flags import flags

    if flags.is_enabled("auto_fix"):
        result = await auto_fix_service.generate_and_apply_fix(...)

    model = flags.get_model_override("pr_review")  # e.g. "gpt-4o-mini"
"""

from __future__ import annotations

import os
from typing import Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Default flag definitions
# ---------------------------------------------------------------------------

_DEFAULTS: dict[str, dict[str, Any]] = {
    # AI features
    "ai_chat": {"enabled": True, "description": "RAG-powered chat"},
    "ai_streaming": {"enabled": True, "description": "Streaming chat responses"},
    "pr_review": {"enabled": True, "description": "Automated PR review"},
    "code_health": {"enabled": True, "description": "Code health analysis"},
    "auto_fix": {"enabled": True, "description": "Autonomous code fixes"},
    "test_generation": {"enabled": True, "description": "AI test generation"},
    "agent_mode": {"enabled": True, "description": "Autonomous agent actions"},
    "architecture_diagrams": {"enabled": True, "description": "Architecture visualization"},
    "code_migration": {"enabled": True, "description": "AI-powered code migration"},
    "policy_checker": {"enabled": True, "description": "Custom policy enforcement"},

    # Infrastructure features
    "hybrid_retrieval": {"enabled": True, "description": "BM25 + Vector hybrid search"},
    "context_expansion": {"enabled": True, "description": "Neighbor chunk expansion"},
    "response_caching": {"enabled": True, "description": "Cache AI responses"},
    "rate_limiting": {"enabled": True, "description": "API rate limiting"},

    # Model overrides (value is the model name, not bool)
    "model_override_chat": {"enabled": False, "value": None, "description": "Override chat model"},
    "model_override_pr_review": {"enabled": False, "value": None, "description": "Override PR review model"},
    "model_override_embedding": {"enabled": False, "value": None, "description": "Override embedding model"},
}


# ---------------------------------------------------------------------------
# Feature flag registry
# ---------------------------------------------------------------------------


class FeatureFlags:
    """Centralized feature flag registry.

    Flags can be toggled via environment variables:
    ``FEATURE_FLAG_AUTO_FIX=false`` disables the ``auto_fix`` flag.
    """

    def __init__(self) -> None:
        self._flags: dict[str, dict[str, Any]] = {}
        self._load_defaults()
        self._apply_env_overrides()

    def _load_defaults(self) -> None:
        """Load default flag definitions."""
        for name, config in _DEFAULTS.items():
            self._flags[name] = {**config}

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides.

        Format: ``FEATURE_FLAG_<UPPERCASE_NAME>=true|false``
        For value flags: ``FEATURE_FLAG_<UPPERCASE_NAME>=<value>``
        """
        for name in self._flags:
            env_key = f"FEATURE_FLAG_{name.upper()}"
            env_val = os.environ.get(env_key)

            if env_val is not None:
                # Bool flags
                if env_val.lower() in ("true", "1", "yes"):
                    self._flags[name]["enabled"] = True
                    logger.info("Feature flag '%s' enabled via env", name)
                elif env_val.lower() in ("false", "0", "no"):
                    self._flags[name]["enabled"] = False
                    logger.info("Feature flag '%s' disabled via env", name)
                else:
                    # Value override (e.g., model name)
                    self._flags[name]["enabled"] = True
                    self._flags[name]["value"] = env_val
                    logger.info("Feature flag '%s' set to '%s' via env", name, env_val)

    def is_enabled(self, name: str) -> bool:
        """Check if a feature flag is enabled.

        Args:
            name: Flag name (e.g., "auto_fix").

        Returns:
            True if the flag is enabled, False otherwise.
            Unknown flags return False.
        """
        flag = self._flags.get(name)
        if flag is None:
            logger.warning("Unknown feature flag: %s", name)
            return False
        return bool(flag.get("enabled", False))

    def get_value(self, name: str) -> Optional[str]:
        """Get the value of a value-type flag (e.g., model override).

        Returns:
            The flag value, or None if not set or disabled.
        """
        flag = self._flags.get(name)
        if flag is None or not flag.get("enabled"):
            return None
        return flag.get("value")

    def get_model_override(self, agent: str) -> Optional[str]:
        """Get model override for a specific agent/operation.

        Checks ``model_override_<agent>`` flag.

        Args:
            agent: Agent name (e.g., "chat", "pr_review").

        Returns:
            Model name string, or None (use default).
        """
        return self.get_value(f"model_override_{agent}")

    def set(self, name: str, enabled: bool) -> None:
        """Dynamically set a flag at runtime.

        Args:
            name: Flag name.
            enabled: Whether the flag should be enabled.
        """
        if name in self._flags:
            self._flags[name]["enabled"] = enabled
            logger.info("Feature flag '%s' set to %s", name, enabled)
        else:
            self._flags[name] = {"enabled": enabled, "description": "runtime flag"}
            logger.info("Feature flag '%s' created and set to %s", name, enabled)

    def list_flags(self) -> list[dict[str, Any]]:
        """Return all flags with their current state."""
        return [
            {
                "name": name,
                "enabled": config.get("enabled", False),
                "description": config.get("description", ""),
                "value": config.get("value"),
            }
            for name, config in sorted(self._flags.items())
        ]

    def __contains__(self, name: str) -> bool:
        return name in self._flags


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """Return the global FeatureFlags singleton."""
    global _flags
    if _flags is None:
        _flags = FeatureFlags()
    return _flags


# Convenience alias
flags = get_feature_flags()
