"""Test that file_parser produces OS-portable forward-slash paths.

Verifies the fix: Path.as_posix() always produces forward slashes
regardless of whether the OS is Windows (backslash) or Unix (forward slash).
"""

import os
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest

from app.utils.file_parser import parse_repository_files


class TestFilePathSeparators:
    """Verify file_parser always produces forward-slash paths."""

    def test_as_posix_produces_forward_slashes(self):
        """Path.as_posix() always returns forward slashes — the core invariant."""
        win_path = PureWindowsPath("src\\itsdangerous\\signer.py")
        assert win_path.as_posix() == "src/itsdangerous/signer.py"

        unix_path = PurePosixPath("src/itsdangerous/signer.py")
        assert unix_path.as_posix() == "src/itsdangerous/signer.py"

    def test_relative_to_as_posix(self):
        """Verify the exact pattern used in file_parser.py line 63."""
        if os.name == "nt":
            base = Path("C:/tmp/repo")
            full = Path("C:/tmp/repo/src/itsdangerous/signer.py")
        else:
            base = Path("/tmp/repo")
            full = Path("/tmp/repo/src/itsdangerous/signer.py")

        result = full.relative_to(base).as_posix()
        assert result == "src/itsdangerous/signer.py"
        assert "\\" not in result

    def test_parse_repository_files_produces_forward_slashes(self, tmp_path):
        """Integration test: parse_repository_files returns forward-slash paths."""
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)

        test_file = src_dir / "module.py"
        test_file.write_text("def hello(): pass\n", encoding="utf-8")

        files_data = parse_repository_files(str(tmp_path))

        assert len(files_data) == 1
        file_path, content = files_data[0]

        assert file_path == "src/mypackage/module.py"
        assert "\\" not in file_path
        assert "def hello" in content

    def test_parse_repository_deeply_nested_forward_slashes(self, tmp_path):
        """Deeply nested paths also produce forward slashes."""
        deep_dir = tmp_path / "a" / "b" / "c" / "d"
        deep_dir.mkdir(parents=True)
        (deep_dir / "deep.py").write_text("x = 1\n", encoding="utf-8")

        files_data = parse_repository_files(str(tmp_path))

        assert len(files_data) == 1
        assert files_data[0][0] == "a/b/c/d/deep.py"
        assert "\\" not in files_data[0][0]
