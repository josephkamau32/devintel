"""Tests for app.utils.patcher — unified diff patcher with validation."""

import pytest

from app.utils.patcher import PatcherError, UnifiedDiffPatcher, apply_unified_diff

SAMPLE_ORIGINAL = """def hello():
    print("Hello, world!")
    return True

def goodbye():
    print("Goodbye!")
"""

VALID_DIFF_SINGLE_HUNK = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello, world!")
+    print("Hello, DevIntel!")
     return True
"""

VALID_DIFF_MULTI_HUNK = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def hello():
-    print("Hello, world!")
+    print("Hello, DevIntel!")
     return True
@@ -5,2 +5,2 @@
 def goodbye():
-    print("Goodbye!")
+    print("See you later!")
"""


# ======================================================================
# Successful patch application
# ======================================================================

class TestApplyPatchSuccess:
    def test_single_hunk_replaces_line_accurately(self):
        result = UnifiedDiffPatcher.apply_patch(SAMPLE_ORIGINAL, VALID_DIFF_SINGLE_HUNK)
        expected = """def hello():
    print("Hello, DevIntel!")
    return True

def goodbye():
    print("Goodbye!")
"""
        assert result == expected

    def test_multi_hunk_applies_all_modifications(self):
        result = UnifiedDiffPatcher.apply_patch(SAMPLE_ORIGINAL, VALID_DIFF_MULTI_HUNK)
        assert 'print("Hello, DevIntel!")' in result
        assert 'print("See you later!")' in result
        assert 'print("Hello, world!")' not in result
        assert 'print("Goodbye!")' not in result
        assert 'def goodbye():' in result

    def test_apply_unified_diff_convenience_function(self):
        result = apply_unified_diff(SAMPLE_ORIGINAL, VALID_DIFF_SINGLE_HUNK)
        assert 'print("Hello, DevIntel!")' in result

    def test_addition_of_new_lines(self):
        diff = """--- a/test.py
+++ b/test.py
@@ -1,2 +1,3 @@
 def hello():
+    # Log greeting
     print("Hello, world!")
"""
        result = UnifiedDiffPatcher.apply_patch(SAMPLE_ORIGINAL, diff)
        assert "# Log greeting" in result
        assert 'print("Hello, world!")' in result


# ======================================================================
# Error conditions and validation
# ======================================================================

class TestApplyPatchErrors:
    def test_empty_original_content_raises_error(self):
        with pytest.raises(PatcherError, match="Original content cannot be empty"):
            UnifiedDiffPatcher.apply_patch("", VALID_DIFF_SINGLE_HUNK)

    def test_empty_patch_content_raises_error(self):
        with pytest.raises(PatcherError, match="Patch content cannot be empty"):
            UnifiedDiffPatcher.apply_patch(SAMPLE_ORIGINAL, "")

    def test_whitespace_only_patch_raises_error(self):
        with pytest.raises(PatcherError, match="Patch content cannot be empty"):
            UnifiedDiffPatcher.apply_patch(SAMPLE_ORIGINAL, "   \n\t  ")

    def test_patch_without_valid_hunks_raises_error(self):
        invalid_diff = "--- a/test.py\n+++ b/test.py\nJust some plain text without diff markers\n"
        with pytest.raises(PatcherError, match="No valid hunks found in patch"):
            UnifiedDiffPatcher.apply_patch(SAMPLE_ORIGINAL, invalid_diff)

    def test_context_mismatch_raises_error(self):
        mismatched_diff = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def non_existent_function():
-    do_something()
+    do_another_thing()
"""
        with pytest.raises(PatcherError, match="Context mismatch at line 1"):
            UnifiedDiffPatcher.apply_patch(SAMPLE_ORIGINAL, mismatched_diff)
