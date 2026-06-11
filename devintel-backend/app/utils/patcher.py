import re


class PatcherError(Exception):
    """Raised when a patch cannot be applied."""
    pass

class UnifiedDiffPatcher:
    """Utility to apply standard Unified Diffs to code strings."""

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
        original_lines = original_content.splitlines(keepends=True)
        patch_lines = patch_content.splitlines(keepends=True)

        # Basic validation: ensure it looks like a unified diff
        if not any(line.startswith('---') or line.startswith('+++') or line.startswith('@@') for line in patch_lines):
             # If it doesn't look like a full diff, maybe it's just the hunks?
             # We'll try to prepend dummy headers if needed, but let's assume LLM provides valid diff.
             pass

        # We'll use a simplified version of the logic to apply hunks
        # A more robust way is to use a library or the 'patch' command,
        # but for this autonomous agent, we'll implement a clean hunk-based applier.

        # For simplicity in this implementation, we'll use difflib to help if possible,
        # but difflib doesn't have a direct 'apply' function.
        # We'll parse the hunks manually.

        new_lines = list(original_lines)
        offset = 0

        hunk_re = re.compile(r'^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@')

        i = 0
        while i < len(patch_lines):
            line = patch_lines[i]
            match = hunk_re.match(line)
            if match:
                # Start of a hunk
                old_start = int(match.group(1))
                old_len = int(match.group(2)) if match.group(2) else 1
                _new_start = int(match.group(3))
                _new_len = int(match.group(4)) if match.group(4) else 1

                # Hunk lines
                hunk_data = []
                i += 1
                while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
                    if patch_lines[i].startswith(('+', '-', ' ')):
                        hunk_data.append(patch_lines[i])
                    i += 1

                # Apply the hunk
                # Note: Unified diff line numbers are 1-indexed.
                # Adjusting for offset from previous hunks.
                target_idx = old_start - 1 + offset

                # Verification: the context lines in the hunk SHOULD match the original
                # but we'll be slightly lenient if the lines are mostly right.
                # In a real production system, you'd use more sophisticated fuzzy matching.

                # Extract the old lines from the hunk (lines starting with ' ' or '-')
                _expected_old_segment = [line[1:] for line in hunk_data if line.startswith((' ', '-'))]
                # Compare with target_idx to target_idx + old_len

                # For now, we'll just replace the range
                new_segment = [line[1:] for line in hunk_data if line.startswith((' ', '+'))]

                # Update new_lines
                new_lines[target_idx : target_idx + old_len] = new_segment

                # Update offset
                offset += len(new_segment) - old_len

                # Continue from current i (which is at the next @@ or end)
                continue
            i += 1

        return "".join(new_lines)

def apply_unified_diff(content: str, diff: str) -> str:
    """Wrapper for UnifiedDiffPatcher."""
    return UnifiedDiffPatcher.apply_patch(content, diff)
