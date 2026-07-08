import json
import tempfile
import unittest
from pathlib import Path

from scripts.conventions import (
    generate_frontmatter,
    generate_frontmatter_by_type,
    ensure_frontmatter,
    get_attachment_path,
    get_wiki_subdir,
    get_template_path,
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
            "knowledge": {
                "wiki_dir": "wiki",
                "raw_dir": ".raw",
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

    def test_generate_frontmatter_by_type_concept(self):
        fm = generate_frontmatter_by_type("concept", "Test", [], self.config)
        self.assertIn("type: concept", fm)
        self.assertIn("status: seed", fm)
        self.assertIn("complexity: basic", fm)
        self.assertIn("aliases: []", fm)
        self.assertIn("related: []", fm)
        self.assertIn("sources: []", fm)

    def test_generate_frontmatter_by_type_source(self):
        fm = generate_frontmatter_by_type("source", "Source Note", [], self.config)
        self.assertIn("type: source", fm)
        self.assertIn("confidence: medium", fm)
        self.assertIn("key_claims: []", fm)

    def test_generate_frontmatter_by_type_entity(self):
        fm = generate_frontmatter_by_type("entity", "Person", [], self.config)
        self.assertIn("type: entity", fm)
        self.assertIn("entity_type: ", fm)
        self.assertIn("role: ", fm)

    def test_generate_frontmatter_by_type_comparison(self):
        fm = generate_frontmatter_by_type("comparison", "A vs B", [], self.config)
        self.assertIn("type: comparison", fm)
        self.assertIn("subjects: []", fm)
        self.assertIn("verdict: ", fm)

    def test_generate_frontmatter_by_type_question(self):
        fm = generate_frontmatter_by_type("question", "What is X?", [], self.config)
        self.assertIn("type: question", fm)
        self.assertIn("answer_quality: draft", fm)
        self.assertIn("question: ", fm)

    def test_get_wiki_subdir(self):
        self.assertEqual(get_wiki_subdir("concept", self.config), "wiki/concepts")
        self.assertEqual(get_wiki_subdir("entity", self.config), "wiki/entities")
        self.assertEqual(get_wiki_subdir("source", self.config), "wiki/sources")
        self.assertEqual(get_wiki_subdir("unknown", self.config), "wiki")

    def test_get_template_path(self):
        path = get_template_path("concept")
        self.assertTrue(str(path).endswith("_templates\\concept.md") or
                        str(path).endswith("_templates/concept.md"))


if __name__ == "__main__":
    unittest.main()
