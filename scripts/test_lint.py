import tempfile
import unittest
from pathlib import Path

from scripts.lint import run_lint, _parse_frontmatter, _find_wikilinks


class TestLintBasics(unittest.TestCase):
    def test_parse_frontmatter_normal(self):
        fm, body = _parse_frontmatter("---\ntype: concept\ntitle: Test\n---\n\n# Hello")
        self.assertEqual(fm["type"], "concept")
        self.assertEqual(fm["title"], "Test")
        self.assertEqual(body, "# Hello")

    def test_parse_frontmatter_none(self):
        fm, body = _parse_frontmatter("# No frontmatter")
        self.assertEqual(fm, {})
        self.assertEqual(body, "# No frontmatter")

    def test_find_wikilinks(self):
        links = _find_wikilinks("See [[Page A]] and [[folder/Page B]]. Also [[Page C|alias]].")
        self.assertIn("Page A", links)
        self.assertIn("folder/Page B", links)
        self.assertIn("Page C", links)

    def test_run_lint_empty_wiki(self):
        import shutil
        tmp = Path(tempfile.mkdtemp())
        try:
            wiki_path = tmp / "wiki"
            wiki_path.mkdir(parents=True)
            config = {
                "vault": {"path": str(tmp), "name": "test"},
                "knowledge": {"wiki_dir": "wiki", "raw_dir": ".raw", "stale_days": 90},
            }
            result = run_lint(config)
            self.assertIsInstance(result, dict)
            total = sum(len(v) for v in result.values())
            self.assertEqual(total, 0, f"Expected 0 issues in empty wiki, got {total}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
