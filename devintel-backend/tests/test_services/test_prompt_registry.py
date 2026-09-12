"""Tests for app.ai.prompts.registry — prompt template loader and registry."""

import pytest

from app.ai.prompts.registry import (
    PromptRegistry,
    PromptTemplate,
    get_prompt_registry,
)


# ======================================================================
# PromptTemplate
# ======================================================================

class TestPromptTemplate:
    def test_init_and_attributes(self):
        data = {
            "name": "test_prompt",
            "version": "2.1.0",
            "description": "A test prompt description",
            "messages": [{"role": "system", "content": "Hello $name"}],
            "model": "gpt-4o",
            "temperature": 0.5,
            "max_tokens": 500,
            "tags": ["unit-test"],
        }
        tpl = PromptTemplate(data, file_path="/fake/path.yaml")
        assert tpl.name == "test_prompt"
        assert tpl.version == "2.1.0"
        assert tpl.description == "A test prompt description"
        assert tpl.model == "gpt-4o"
        assert tpl.temperature == 0.5
        assert tpl.max_tokens == 500
        assert tpl.tags == ["unit-test"]
        assert repr(tpl) == "PromptTemplate(name='test_prompt', version='2.1.0')"

    def test_render_substitutes_variables(self):
        data = {
            "name": "greeting",
            "messages": [
                {"role": "system", "content": "You are assistant for $repo."},
                {"role": "user", "content": "Analyze $file_path at line $line_no."},
            ],
        }
        tpl = PromptTemplate(data)
        rendered = tpl.render(repo="devintel-core", file_path="main.py", line_no="42")
        assert len(rendered) == 2
        assert rendered[0] == {"role": "system", "content": "You are assistant for devintel-core."}
        assert rendered[1] == {"role": "user", "content": "Analyze main.py at line 42."}

    def test_render_safe_substitute_keeps_unprovided_vars(self):
        data = {
            "name": "partial",
            "messages": [{"role": "user", "content": "Hello $name, your score is $score"}],
        }
        tpl = PromptTemplate(data)
        rendered = tpl.render(name="Alice")
        assert rendered[0]["content"] == "Hello Alice, your score is $score"


# ======================================================================
# PromptRegistry
# ======================================================================

class TestPromptRegistry:
    def test_loads_shipped_templates(self):
        registry = PromptRegistry()
        # Ensure that known shipped templates exist
        assert len(registry) >= 4
        assert "chat_system" in registry
        assert "pr_review" in registry
        assert "auto_fix" in registry

    def test_get_existing_template(self):
        registry = PromptRegistry()
        tpl = registry.get("chat_system")
        assert isinstance(tpl, PromptTemplate)
        assert tpl.name == "chat_system"
        assert len(tpl.messages_raw) >= 1

    def test_get_missing_template_raises_key_error_with_helpful_message(self):
        registry = PromptRegistry()
        with pytest.raises(KeyError) as exc_info:
            registry.get("nonexistent_template_xyz")
        assert "Prompt template 'nonexistent_template_xyz' not found" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)

    def test_list_templates_returns_metadata(self):
        registry = PromptRegistry()
        templates_list = registry.list_templates()
        assert isinstance(templates_list, list)
        names = [t["name"] for t in templates_list]
        assert "chat_system" in names
        sample = next(t for t in templates_list if t["name"] == "chat_system")
        assert "version" in sample
        assert "description" in sample
        assert "tags" in sample

    def test_reload_repopulates_templates(self):
        registry = PromptRegistry()
        initial_len = len(registry)
        registry.reload()
        assert len(registry) == initial_len
        assert "chat_system" in registry

    def test_singleton_get_prompt_registry(self):
        reg1 = get_prompt_registry()
        reg2 = get_prompt_registry()
        assert reg1 is reg2
