import json
import tempfile
import unittest
from pathlib import Path

from scripts.conventions import (
    generate_frontmatter,
    ensure_frontmatter,
    get_attachment_path,
    format_wikilink,
)


class TestConventions(unittest.TestCase):
    def setUp(self):
        self.config = {
            "vault": {"path": "D:/vault"},
            "conventions": {
                "attachment_dir": "attachments",
                "frontmatter": {
                    "required_fields": ["title", "tags", "created", "modified"],
                    "date_format": "YYYY-MM-DD HH:mm:ss",
                },
            },
        }

    def test_generate_frontmatter_has_all_fields(self):
        fm = generate_frontmatter("My Note", ["tag1"], self.config)
        self.assertIn("title: My Note", fm)
        self.assertIn("tags: [tag1]", fm)
        self.assertIn("created:", fm)
        self.assertIn("modified:", fm)
        self.assertTrue(fm.startswith("---"))
        self.assertTrue(fm.endswith("\n"))

    def test_generate_frontmatter_no_tags(self):
        fm = generate_frontmatter("Note", [], self.config)
        self.assertIn("tags: []", fm)

    def test_ensure_frontmatter_adds_when_missing(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("# Hello\n\nSome content\n")
            tmp_path = Path(f.name)
        try:
            ensure_frontmatter(tmp_path, self.config)
            content = tmp_path.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---"))
            self.assertIn("title:", content)
        finally:
            tmp_path.unlink()

    def test_ensure_frontmatter_skips_when_present(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("---\ntitle: X\n---\n\n# Hello\n")
            tmp_path = Path(f.name)
        try:
            original = tmp_path.read_text(encoding="utf-8")
            ensure_frontmatter(tmp_path, self.config)
            self.assertEqual(original, tmp_path.read_text(encoding="utf-8"))
        finally:
            tmp_path.unlink()

    def test_get_attachment_path(self):
        result = get_attachment_path(self.config, "img.png")
        self.assertEqual(result, Path("D:/vault/attachments/img.png"))

    def test_format_wikilink(self):
        self.assertEqual(format_wikilink("notes/My Note"), "[[notes/My Note]]")
        self.assertEqual(format_wikilink("attachments/img.png"), "[[attachments/img.png]]")


if __name__ == "__main__":
    unittest.main()
