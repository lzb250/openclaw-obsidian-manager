import unittest
from pathlib import Path

from scripts.sync import init_repo


class TestSync(unittest.TestCase):
    def test_init_repo_creates_git_dir(self):
        import tempfile
        import shutil
        tmp = Path(tempfile.mkdtemp())
        try:
            init_repo(tmp, "https://example.com/repo.git", "main")
            self.assertTrue((tmp / ".git").exists())
            import subprocess
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=str(tmp), capture_output=True, text=True
            )
            self.assertIn("example.com/repo.git", result.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
