import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.init_vault import WIKI_DIRS


class TestInitVault(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.config = {
            "vault": {"path": str(self.tmp), "name": "test-vault"},
            "git": {"remote": "", "branch": "main", "auto_sync_minutes": 30},
            "conventions": {
                "attachment_dir": "attachments",
                "daily_dir": "daily",
                "template_dir": "templates",
                "frontmatter": {"date_format": "YYYY-MM-DD HH:mm:ss"},
                "wikilinks": True,
            },
            "knowledge": {
                "wiki_dir": "wiki",
                "raw_dir": ".raw",
                "hot_cache_words": 500,
                "stale_days": 90,
            },
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    @patch("scripts.init_vault.subprocess.run")
    def test_run_init_creates_structure(self, mock_run):
        mock_run.return_value.returncode = 0
        from scripts.init_vault import run_init
        run_init(self.config)

        wiki_path = self.tmp / "wiki"
        self.assertTrue(wiki_path.exists())
        for d in WIKI_DIRS:
            self.assertTrue((wiki_path / d).exists(), f"Missing: {d}")

        self.assertTrue((self.tmp / ".raw").exists())
        self.assertTrue((self.tmp / "_templates").exists())
        self.assertTrue((self.tmp / "attachments").exists())
        self.assertTrue((self.tmp / ".obsidian" / "app.json").exists())
        self.assertTrue((self.tmp / ".obsidian" / "graph.json").exists())
        self.assertTrue((wiki_path / "index.md").exists())
        self.assertTrue((wiki_path / "hot.md").exists())
        self.assertTrue((wiki_path / "log.md").exists())
        self.assertTrue((wiki_path / "overview.md").exists())

    @patch("scripts.init_vault.subprocess.run")
    def test_run_init_seed_pages_have_frontmatter(self, mock_run):
        mock_run.return_value.returncode = 0
        from scripts.init_vault import run_init
        run_init(self.config)

        for name in ["index.md", "hot.md", "log.md", "overview.md"]:
            content = (self.tmp / "wiki" / name).read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---"), f"{name} missing frontmatter")


if __name__ == "__main__":
    unittest.main()
