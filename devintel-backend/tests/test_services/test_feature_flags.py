"""Tests for app.core.feature_flags — env overrides, defaults, edge cases."""

import os

import pytest

from app.core.feature_flags import FeatureFlags


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all FEATURE_FLAG_* env vars so each test starts clean."""
    for key in list(os.environ.keys()):
        if key.startswith("FEATURE_FLAG_"):
            monkeypatch.delenv(key)


class TestFeatureFlagsDefaults:
    def test_known_flag_enabled_by_default(self, clean_env):
        ff = FeatureFlags()
        assert ff.is_enabled("ai_chat") is True

    def test_model_override_disabled_by_default(self, clean_env):
        ff = FeatureFlags()
        assert ff.is_enabled("model_override_chat") is False

    def test_unknown_flag_returns_false(self, clean_env):
        ff = FeatureFlags()
        assert ff.is_enabled("totally_nonexistent_flag") is False


class TestEnvOverrides:
    def test_disable_via_env(self, monkeypatch, clean_env):
        monkeypatch.setenv("FEATURE_FLAG_AI_CHAT", "false")
        ff = FeatureFlags()
        assert ff.is_enabled("ai_chat") is False

    def test_enable_via_env_with_1(self, monkeypatch, clean_env):
        monkeypatch.setenv("FEATURE_FLAG_MODEL_OVERRIDE_CHAT", "1")
        ff = FeatureFlags()
        assert ff.is_enabled("model_override_chat") is True

    def test_disable_via_env_with_0(self, monkeypatch, clean_env):
        monkeypatch.setenv("FEATURE_FLAG_AI_CHAT", "0")
        ff = FeatureFlags()
        assert ff.is_enabled("ai_chat") is False

    def test_disable_via_env_with_no(self, monkeypatch, clean_env):
        monkeypatch.setenv("FEATURE_FLAG_AI_CHAT", "no")
        ff = FeatureFlags()
        assert ff.is_enabled("ai_chat") is False

    def test_enable_via_env_with_yes(self, monkeypatch, clean_env):
        monkeypatch.setenv("FEATURE_FLAG_MODEL_OVERRIDE_CHAT", "yes")
        ff = FeatureFlags()
        assert ff.is_enabled("model_override_chat") is True

    def test_value_override_sets_value_and_enables(self, monkeypatch, clean_env):
        """A non-bool env value (e.g. a model name) enables the flag and sets the value."""
        monkeypatch.setenv("FEATURE_FLAG_MODEL_OVERRIDE_CHAT", "gpt-4o-mini")
        ff = FeatureFlags()
        assert ff.is_enabled("model_override_chat") is True
        assert ff.get_value("model_override_chat") == "gpt-4o-mini"


class TestGetValue:
    def test_returns_none_for_disabled_flag(self, clean_env):
        ff = FeatureFlags()
        assert ff.get_value("model_override_chat") is None

    def test_returns_none_for_unknown_flag(self, clean_env):
        ff = FeatureFlags()
        assert ff.get_value("does_not_exist") is None

    def test_returns_none_for_bool_flag_without_value(self, clean_env):
        ff = FeatureFlags()
        # ai_chat is enabled=True but has no "value" key
        assert ff.get_value("ai_chat") is None


class TestGetModelOverride:
    def test_returns_none_when_no_override(self, clean_env):
        ff = FeatureFlags()
        assert ff.get_model_override("chat") is None

    def test_returns_model_name_when_set(self, monkeypatch, clean_env):
        monkeypatch.setenv("FEATURE_FLAG_MODEL_OVERRIDE_PR_REVIEW", "gemini-pro")
        ff = FeatureFlags()
        assert ff.get_model_override("pr_review") == "gemini-pro"


class TestSetAndContains:
    def test_set_existing_flag(self, clean_env):
        ff = FeatureFlags()
        ff.set("ai_chat", False)
        assert ff.is_enabled("ai_chat") is False

    def test_set_creates_new_flag(self, clean_env):
        ff = FeatureFlags()
        ff.set("brand_new_flag", True)
        assert ff.is_enabled("brand_new_flag") is True
        assert "brand_new_flag" in ff

    def test_contains_known_flag(self, clean_env):
        ff = FeatureFlags()
        assert "ai_chat" in ff

    def test_not_contains_unknown(self, clean_env):
        ff = FeatureFlags()
        assert "no_such_flag" not in ff


class TestListFlags:
    def test_list_returns_all_flags(self, clean_env):
        ff = FeatureFlags()
        listed = ff.list_flags()
        names = [f["name"] for f in listed]
        assert "ai_chat" in names
        assert "model_override_chat" in names
        # Each entry has expected keys
        sample = listed[0]
        assert "enabled" in sample
        assert "description" in sample
        assert "name" in sample
