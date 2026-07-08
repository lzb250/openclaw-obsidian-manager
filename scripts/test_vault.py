import json
import tempfile
import unittest
from pathlib import Path

from scripts.vault import _get_note_path, _get_vault_name


class TestVault(unittest.TestCase):
    def setUp(self):
        self.config = {
            "vault": {"path": "D:/vault", "name": "my-vault"},
            "conventions": {
                "attachment_dir": "attachments",
                "daily_dir": "daily",
                "frontmatter": {
                    "required_fields": ["title", "tags", "created", "modified"],
                    "date_format": "YYYY-MM-DD HH:mm:ss",
                },
            },
            "git": {"remote": "", "branch": "main", "auto_sync_minutes": 30},
        }

    def test_get_vault_name_from_path(self):
        self.assertEqual(_get_vault_name(self.config), "vault")

    def test_get_note_path_adds_md_extension(self):
        result = _get_note_path(self.config, "My Note")
        self.assertEqual(result, Path("D:/vault/My Note.md"))

    def test_get_note_path_keeps_extension(self):
        result = _get_note_path(self.config, "readme.txt")
        self.assertEqual(result, Path("D:/vault/readme.txt"))


if __name__ == "__main__":
    unittest.main()
