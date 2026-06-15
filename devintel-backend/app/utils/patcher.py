"""Robust unified diff patcher with validation and error handling."""

import difflib
import re


class PatcherError(Exception):
    """Raised when a patch cannot be applied."""
    pass


class UnifiedDiffPatcher:
    """Utility to apply standard Unified Diffs to code strings with validation."""

    @staticmethod
    def apply_patch(original_content: str, patch_content: str) -> str:
        """
        Applies a unified diff to the original content.

        Args:
            original_content: The original source code as a string.
            patch_content: The unified diff as a string.

        Returns:
            The patched source code.

        Raises:
            PatcherError: If the patch is malformed or cannot be applied.
        """
        if not original_content:
            raise PatcherError("Original content cannot be empty")

        if not patch_content or not patch_content.strip():
            raise PatcherError("Patch content cannot be empty")

        original_lines = original_content.splitlines(keepends=True)
        patch_lines = patch_content.splitlines(keepends=True)

        # Parse hunks from the diff
        hunks = UnifiedDiffPatcher._parse_hunks(patch_lines)

        if not hunks:
            raise PatcherError("No valid hunks found in patch")

        new_lines = list(original_lines)
        cumulative_offset = 0

        for hunk in hunks:
            old_start, old_count, new_start, new_count, hunk_lines = hunk

            # Apply with offset adjustment
            target_idx = old_start - 1 + cumulative_offset

            # Extract old and new segments
            old_segment = [line[1:] for line in hunk_lines if line.startswith((' ', '-'))]
            new_segment = [line[1:] for line in hunk_lines if line.startswith((' ', '+'))]

            # Validate context (fuzzy matching for robustness)
            if not UnifiedDiffPatcher._validate_context(
                original_lines, target_idx, old_segment, old_count
            ):
                # Try to find the context in the file (fallback matching)
                found_idx = UnifiedDiffPatcher._find_fuzzy_match(
                    original_lines, old_segment
                )
                if found_idx is not None:
                    target_idx = found_idx
                    cumulative_offset += found_idx - (old_start - 1)
                else:
                    raise PatcherError(
                        f"Context mismatch at line {old_start}: "
                        f"expected lines not found in original content"
                    )

            # Replace the segment
            if target_idx + old_count - cumulative_offset > len(new_lines):
                raise PatcherError(
                    f"Patch extends beyond file length at line {target_idx}"
                )

            new_lines[target_idx + cumulative_offset : target_idx + old_count - cumulative_offset] = new_segment

            # Update offset for next hunk
            cumulative_offset += len(new_segment) - old_count

        return "".join(new_lines)

    @staticmethod
    def _parse_hunks(patch_lines: list[str]) -> list[tuple[int, int, int, int, list[str]]]:
        """Parse unified diff hunks.

        Returns list of (old_start, old_count, new_start, new_count, hunk_lines).
        """
        hunks = []
        hunk_re = re.compile(r'^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@')

        i = 0
        while i < len(patch_lines):
            if not patch_lines[i].startswith('@@'):
                i += 1
                continue

            match = hunk_re.match(patch_lines[i])
            if not match:
                i += 1
                continue

            old_start = int(match.group(1))
            old_count = int(match.group(2)) if match.group(2) else 1
            new_start = int(match.group(3))
            new_count = int(match.group(4)) if match.group(4) else 1

            i += 1
            hunk_lines = []
            while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
                if patch_lines[i].startswith(('+', '-', ' ')):
                    hunk_lines.append(patch_lines[i])
                i += 1

            hunks.append((old_start, old_count, new_start, new_count, hunk_lines))

        return hunks

    @staticmethod
    def _validate_context(
        original_lines: list[str],
        target_idx: int,
        expected_old: list[str],
        old_count: int,
    ) -> bool:
        """Validate that context lines match the original."""
        if target_idx < 0 or target_idx >= len(original_lines):
            return False

        # Get the actual lines at the target position
        end_idx = min(target_idx + old_count, len(original_lines))
        actual_lines = original_lines[target_idx:end_idx]

        # Use difflib for fuzzy matching
        matcher = difflib.SequenceMatcher(None, expected_old, actual_lines)
        return matcher.ratio() >= 0.8  # Accept 80% similarity

    @staticmethod
    def _find_fuzzy_match(
        original_lines: list[str],
        search_lines: list[str],
    ) -> int | None:
        """Find a fuzzy match for the search lines in the original."""
        if not search_lines:
            return 0

        for start_idx in range(len(original_lines) - len(search_lines) + 1):
            candidate = original_lines[start_idx : start_idx + len(search_lines)]
            matcher = difflib.SequenceMatcher(None, search_lines, candidate)
            if matcher.ratio() >= 0.85:
                return start_idx

        return None


def apply_unified_diff(content: str, diff: str) -> str:
    """Apply a unified diff to content.

    Args:
        content: Original code content
        diff: Unified diff string

    Returns:
        Patched content

    Raises:
        PatcherError: If patch cannot be applied
    """
    return UnifiedDiffPatcher.apply_patch(content, diff)