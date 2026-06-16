"""Sandbox service for executing generated tests."""

import asyncio
import json
import os
import tempfile
from typing import Optional
from uuid import UUID

from app.core.logging import get_logger
from app.core.exceptions import APIError

logger = get_logger(__name__)


class SandboxService:
    """Execute tests in isolated environment."""

    TEST_TIMEOUT = 30  # seconds

    @staticmethod
    async def run_tests(
        test_content: str,
        patched_files: dict[str, str],
        test_file_path: str,
    ) -> dict:
        """
        Run tests in isolated temporary directory.

        Args:
            test_content: Generated test file content
            patched_files: Dictionary of {path: content} for patched source files
            test_file_path: Path of the test file

        Returns:
            Dict with passed (bool), output (str), and test results
        """
        temp_dir = tempfile.mkdtemp(prefix="devintel_test_")

        try:
            # Write patched files to temp directory
            for path, content in patched_files.items():
                full_path = os.path.join(temp_dir, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Write test file
            test_full_path = os.path.join(temp_dir, test_file_path)
            os.makedirs(os.path.dirname(test_full_path), exist_ok=True)
            with open(test_full_path, "w", encoding="utf-8") as f:
                f.write(test_content)

            # Run pytest
            proc = await asyncio.create_subprocess_exec(
                "python", "-m", "pytest", test_file_path,
                "--tb=short",
                "--json-report", "--json-report-file=-",
                cwd=temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=SandboxService.TEST_TIMEOUT
                )
            except asyncio.TimeoutError:
                proc.kill()
                return {
                    "passed": False,
                    "output": f"Test execution timed out after {SandboxService.TEST_TIMEOUT}s",
                    "error": "timeout"
                }

            output = stdout.decode("utf-8", errors="replace")

            # Parse json report if available
            try:
                report = json.loads(output)
                passed = report.get("summary", {}).get("passed", 0) > 0
                return {
                    "passed": passed,
                    "output": output,
                    "summary": report.get("summary", {}),
                }
            except json.JSONDecodeError:
                # No JSON report, check exit code
                passed = proc.returncode == 0
                return {
                    "passed": passed,
                    "output": output + "\n" + stderr.decode("utf-8", errors="replace"),
                }

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return {
                "passed": False,
                "output": str(e),
                "error": "execution_failed"
            }
        finally:
            # Cleanup
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass