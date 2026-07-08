# Obsidian Manager Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI skill for openclaw that manages an Obsidian vault via notesmd-cli with git auto-sync.

**Architecture:** Python 3 stdlib-only scripts under `scripts/` with modular separation: `config.py` (JSON read/write), `conventions.py` (Obsidian formatting rules), `sync.py` (git pull/push), `vault.py` (notesmd-cli wrapper), and `obsidian_mgr.py` (argparse CLI router). SKILL.md and `docs/` provide progressive disclosure documentation.

**Tech Stack:** Python >= 3.8 (stdlib only), notesmd-cli (Go binary), git (system)

## Global Constraints

- Python >= 3.8, stdlib only (no pip packages)
- notesmd-cli must be installed separately (scoop on Windows, homebrew on macOS/Linux)
- git must be available on system PATH
- Config file `obsidian-manager.json` at project root
- SKILL.md is minimal entry point; detailed docs in `docs/`
- All scripts discover config via `Path(__file__).resolve().parent.parent / "obsidian-manager.json"`

---

### Task 1: Config Module

**Files:**
- Create: `scripts/config.py`

**Interfaces:**
- Consumes: (none — first module)
- Produces:
  - `load_config() -> dict` — reads `obsidian-manager.json` from project root, returns parsed dict
  - `save_config(config: dict) -> None` — writes dict back to `obsidian-manager.json`
  - `get_config_path() -> Path` — returns resolved path to config file

- [ ] **Step 1: Create `scripts/__init__.py` and `scripts/config.py`**

Create an empty `scripts/__init__.py` (makes `scripts` a Python package):

```python
```

Now create `scripts/config.py`:

```python
import json
import sys
from pathlib import Path


def get_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "obsidian-manager.json"


def load_config() -> dict:
    config_path = get_config_path()
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        print("Run 'python scripts/obsidian_mgr.py init' to set up.", file=sys.stderr)
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")
```

- [ ] **Step 2: Verify**

Run `python -c "from scripts.config import get_config_path; print(get_config_path())"` — should print the absolute path to `obsidian-manager.json`.

- [ ] **Step 3: Commit**

```bash
git add scripts/__init__.py scripts/config.py
git commit -m "feat: add config module (load/save JSON config)"
```

---

### Task 2: Conventions Module

**Files:**
- Create: `scripts/conventions.py`

**Interfaces:**
- Consumes: `config.load_config` (from Task 1)
- Produces:
  - `generate_frontmatter(title: str, tags: list[str], config: dict) -> str` — returns YAML frontmatter block string
  - `ensure_frontmatter(note_path: Path, config: dict) -> None` — reads note file, prepends frontmatter if absent
  - `get_attachment_path(config: dict, filename: str) -> Path` — returns `vault_path/attachment_dir/filename`
  - `format_wikilink(relative_path: str) -> str` — returns `[[relative_path]]`

- [ ] **Step 1: Create `scripts/conventions.py`**

```python
from datetime import datetime
from pathlib import Path

from scripts.config import load_config


def generate_frontmatter(title: str, tags: list[str], config: dict) -> str:
    fmt = config["conventions"]["frontmatter"]["date_format"]
    now = datetime.now().strftime(fmt)
    fields = config["conventions"]["frontmatter"]["required_fields"]
    lines = ["---"]
    for field in fields:
        if field == "title":
            lines.append(f"title: {title}")
        elif field == "tags":
            tag_str = ", ".join(tags) if tags else ""
            lines.append(f"tags: [{tag_str}]")
        elif field == "created":
            lines.append(f"created: {now}")
        elif field == "modified":
            lines.append(f"modified: {now}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def ensure_frontmatter(note_path: Path, config: dict) -> None:
    if not note_path.exists():
        return
    content = note_path.read_text(encoding="utf-8")
    if content.startswith("---"):
        return
    title = note_path.stem
    fm = generate_frontmatter(title, [], config)
    note_path.write_text(fm + content, encoding="utf-8")


def get_attachment_path(config: dict, filename: str) -> Path:
    vault_path = Path(config["vault"]["path"])
    attach_dir = config["conventions"]["attachment_dir"]
    return vault_path / attach_dir / filename


def format_wikilink(relative_path: str) -> str:
    return f"[[{relative_path}]]"
```

- [ ] **Step 2: Write unit test `scripts/test_conventions.py`**

```python
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
```

- [ ] **Step 3: Run tests, verify they pass**

Run: `python -m scripts.test_conventions`
Expected: all 6 tests PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/conventions.py scripts/test_conventions.py
git commit -m "feat: add conventions module (frontmatter, wikilinks, attachment path)"
```

---

### Task 3: Sync Module

**Files:**
- Create: `scripts/sync.py`

**Interfaces:**
- Consumes: `config.load_config` (from Task 1)
- Produces:
  - `run_sync(config: dict) -> bool` — full sync: pull → add → commit → push, returns True on success
  - `init_repo(vault_path: Path, remote: str, branch: str) -> None` — git init + remote add

- [ ] **Step 1: Create `scripts/sync.py`**

```python
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from scripts.config import load_config


def _run_git(vault_path: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(vault_path),
        capture_output=True,
        text=True,
    )


def init_repo(vault_path: Path, remote: str, branch: str) -> None:
    if not (vault_path / ".git").exists():
        _run_git(vault_path, ["init"])
        _run_git(vault_path, ["checkout", "-b", branch])
        _run_git(vault_path, ["remote", "add", "origin", remote])
        _run_git(vault_path, ["add", "-A"])
        _run_git(vault_path, ["commit", "-m", "init: initial vault commit"])
        print(f"Initialized git repo at {vault_path}")


def run_sync(config: dict) -> bool:
    vault_path = Path(config["vault"]["path"])
    remote = config["git"]["remote"]
    branch = config["git"]["branch"]

    if not vault_path.exists():
        print(f"Vault path not found: {vault_path}", file=sys.stderr)
        return False

    init_repo(vault_path, remote, branch)

    # Pull (conflicts keep local)
    pull_result = _run_git(vault_path, ["pull", "--rebase", "-X", "theirs", "origin", branch])
    if pull_result.returncode != 0:
        print(f"Pull failed: {pull_result.stderr.strip()}", file=sys.stderr)

    # Stage all changes
    _run_git(vault_path, ["add", "-A"])

    # Check if there are staged changes
    diff_result = _run_git(vault_path, ["diff", "--cached", "--quiet"])
    if diff_result.returncode == 0:
        print("No changes to sync.")
        return True

    # Commit
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"auto: sync {now}"
    commit_result = _run_git(vault_path, ["commit", "-m", commit_msg])
    if commit_result.returncode != 0:
        print(f"Commit failed: {commit_result.stderr.strip()}", file=sys.stderr)
        return False

    # Push
    push_result = _run_git(vault_path, ["push", "origin", branch])
    if push_result.returncode != 0:
        print(f"Push failed (network?): {push_result.stderr.strip()}", file=sys.stderr)
        return False

    print(f"Synced: {commit_msg}")
    return True
```

- [ ] **Step 2: Write unit test `scripts/test_sync.py`**

```python
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
            # Verify remote
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
```

- [ ] **Step 3: Run tests, verify pass**

Run: `python -m scripts.test_sync`
Expected: test_init_repo PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/sync.py scripts/test_sync.py
git commit -m "feat: add sync module (git pull/push with auto-init)"
```

---

### Task 4: Vault Module

**Files:**
- Create: `scripts/vault.py`

**Interfaces:**
- Consumes: `config.load_config` (Task 1), `conventions.generate_frontmatter`, `conventions.ensure_frontmatter`, `conventions.get_attachment_path`, `conventions.format_wikilink` (Task 2)
- Produces:
  - `create_note(config, name, content, open_note) -> None`
  - `edit_note(config, name, content, append) -> None`
  - `manage_frontmatter(config, name, action, key, value) -> None`
  - `move_note(config, src, dest, open_note) -> None`
  - `search_notes(config, by, query) -> None`
  - `list_vault(config, path) -> None`
  - `print_note(config, name) -> None`
  - `delete_note(config, name) -> None`
  - `daily_note(config, content) -> None`
  - `attach_file(config, file_path, name) -> None`

- [ ] **Step 1: Create `scripts/vault.py`**

```python
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.config import load_config
from scripts.conventions import (
    ensure_frontmatter,
    format_wikilink,
    generate_frontmatter,
    get_attachment_path,
)


def _get_vault_name(config: dict) -> str:
    return Path(config["vault"]["path"]).name


def _run_notesmd(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["notesmd-cli"] + args,
        capture_output=True,
        text=True,
    )


def _get_note_path(config: dict, name: str) -> Path:
    vault_path = Path(config["vault"]["path"])
    note_path = vault_path / name
    if not note_path.suffix:
        note_path = note_path.with_suffix(".md")
    return note_path


def create_note(config: dict, name: str, content: str = None, open_note: bool = False) -> None:
    vault_name = _get_vault_name(config)
    note_path = _get_note_path(config, name)

    args = ["create", name, "--vault", vault_name]
    if content:
        args.extend(["--content", content])
    if open_note:
        args.append("--open")

    result = _run_notesmd(args)
    if result.returncode != 0:
        print(f"Create failed: {result.stderr.strip()}", file=sys.stderr)
        return

    print(result.stdout.strip())

    # Auto-inject frontmatter after creation
    if note_path.exists():
        ensure_frontmatter(note_path, config)
        # Update modified date in frontmatter
        _update_frontmatter_date(note_path, config)


def edit_note(config: dict, name: str, content: str, append: bool = False) -> None:
    vault_name = _get_vault_name(config)
    note_path = _get_note_path(config, name)

    if not note_path.exists():
        print(f"Note not found: {name}", file=sys.stderr)
        return

    if append:
        # Append content to existing note
        existing = note_path.read_text(encoding="utf-8")
        note_path.write_text(existing + "\n" + content, encoding="utf-8")
    else:
        # Overwrite via notesmd-cli create --overwrite
        args = ["create", name, "--vault", vault_name, "--content", content, "--overwrite"]
        result = _run_notesmd(args)
        if result.returncode != 0:
            print(f"Edit failed: {result.stderr.strip()}", file=sys.stderr)
            return

    # Ensure frontmatter exists and update modified date
    ensure_frontmatter(note_path, config)
    _update_frontmatter_date(note_path, config)
    print(f"Updated: {name}")


def _update_frontmatter_date(note_path: Path, config: dict) -> None:
    content = note_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return
    from datetime import datetime
    fmt = config["conventions"]["frontmatter"]["date_format"]
    now = datetime.now().strftime(fmt)
    lines = content.split("\n")
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("modified:"):
            lines[i] = f"modified: {now}"
            updated = True
            break
    if updated:
        note_path.write_text("\n".join(lines), encoding="utf-8")


def manage_frontmatter(config: dict, name: str, action: str, key: str = None, value: str = None) -> None:
    vault_name = _get_vault_name(config)
    args = ["frontmatter", name, "--vault", vault_name]
    if action == "print":
        args.append("--print")
    elif action == "set":
        args.extend(["--edit", "--key", key, "--value", value])
    elif action == "delete":
        args.extend(["--delete", "--key", key])

    result = _run_notesmd(args)
    if result.returncode != 0:
        print(f"Frontmatter operation failed: {result.stderr.strip()}", file=sys.stderr)
        return
    print(result.stdout.strip())


def move_note(config: dict, src: str, dest: str, open_note: bool = False) -> None:
    vault_name = _get_vault_name(config)
    args = ["move", src, dest, "--vault", vault_name]
    if open_note:
        args.append("--open")

    result = _run_notesmd(args)
    if result.returncode != 0:
        print(f"Move failed: {result.stderr.strip()}", file=sys.stderr)
        return
    print(result.stdout.strip())


def search_notes(config: dict, by: str, query: str) -> None:
    vault_name = _get_vault_name(config)
    if by == "name":
        result = _run_notesmd(["search", "--vault", vault_name])
    else:
        result = _run_notesmd(["search-content", query, "--vault", vault_name, "--no-interactive"])
    if result.returncode != 0:
        print(f"Search failed: {result.stderr.strip()}", file=sys.stderr)
        return
    print(result.stdout.strip())


def list_vault(config: dict, path: str = None) -> None:
    vault_name = _get_vault_name(config)
    args = ["list", "--vault", vault_name]
    if path:
        args.append(path)
    result = _run_notesmd(args)
    if result.returncode != 0:
        print(f"List failed: {result.stderr.strip()}", file=sys.stderr)
        return
    print(result.stdout.strip())


def print_note(config: dict, name: str) -> None:
    vault_name = _get_vault_name(config)
    result = _run_notesmd(["print", name, "--vault", vault_name])
    if result.returncode != 0:
        print(f"Print failed: {result.stderr.strip()}", file=sys.stderr)
        return
    print(result.stdout.strip())


def delete_note(config: dict, name: str) -> None:
    vault_name = _get_vault_name(config)
    result = _run_notesmd(["delete", name, "--vault", vault_name])
    if result.returncode != 0:
        print(f"Delete failed: {result.stderr.strip()}", file=sys.stderr)
        return
    print(result.stdout.strip())


def daily_note(config: dict, content: str = None) -> None:
    vault_name = _get_vault_name(config)
    args = ["daily", "--vault", vault_name]
    if content:
        args.extend(["--content", content])

    result = _run_notesmd(args)
    if result.returncode != 0:
        print(f"Daily note failed: {result.stderr.strip()}", file=sys.stderr)
        return

    print(result.stdout.strip())

    # Find and ensure frontmatter on the daily note
    vault_path = Path(config["vault"]["path"])
    daily_dir = config["conventions"]["daily_dir"]
    daily_path = vault_path / daily_dir
    if daily_path.exists():
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        for f in daily_path.glob("*.md"):
            if today in f.name:
                ensure_frontmatter(f, config)


def attach_file(config: dict, file_path: str, name: str = None) -> None:
    src_path = Path(file_path)
    if not src_path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        return

    if name is None:
        name = src_path.name

    dest_path = get_attachment_path(config, name)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dest_path)

    relative = str(dest_path.relative_to(Path(config["vault"]["path"])))
    wikilink = format_wikilink(relative)
    print(wikilink)
```

- [ ] **Step 2: Write unit test `scripts/test_vault.py`**

```python
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
```

- [ ] **Step 3: Run tests, verify pass**

Run: `python -m scripts.test_vault`
Expected: all 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/vault.py scripts/test_vault.py
git commit -m "feat: add vault module (notesmd-cli wrapper for all note operations)"
```

---

### Task 5: Main CLI Entry Point

**Files:**
- Create: `scripts/obsidian_mgr.py`

**Interfaces:**
- Consumes: `config.load_config` (Task 1), `sync.run_sync` (Task 3), all `vault.*` functions (Task 4)
- Produces: argparse-based CLI with all subcommands

- [ ] **Step 1: Create `scripts/obsidian_mgr.py`**

```python
import argparse
import sys

from scripts.config import load_config, save_config
from scripts.sync import run_sync
from scripts.vault import (
    attach_file,
    create_note,
    daily_note,
    delete_note,
    edit_note,
    list_vault,
    manage_frontmatter,
    move_note,
    print_note,
    search_notes,
)


def cmd_create(args):
    config = load_config()
    create_note(config, args.name, args.content, args.open)


def cmd_edit(args):
    config = load_config()
    edit_note(config, args.name, args.content, args.append)


def cmd_fm(args):
    config = load_config()
    if args.print:
        manage_frontmatter(config, args.name, "print")
    elif args.set:
        manage_frontmatter(config, args.name, "set", args.key, args.value)
    elif args.delete:
        manage_frontmatter(config, args.name, "delete", key=args.key)


def cmd_move(args):
    config = load_config()
    move_note(config, args.src, args.dest, args.open)


def cmd_search(args):
    config = load_config()
    by = "name" if args.name else "content"
    query = args.query
    search_notes(config, by, query)


def cmd_list(args):
    config = load_config()
    list_vault(config, args.path)


def cmd_print(args):
    config = load_config()
    print_note(config, args.name)


def cmd_delete(args):
    config = load_config()
    delete_note(config, args.name)


def cmd_daily(args):
    config = load_config()
    daily_note(config, args.content)


def cmd_attach(args):
    config = load_config()
    attach_file(config, args.file, args.name)


def cmd_sync(args):
    config = load_config()
    success = run_sync(config)
    sys.exit(0 if success else 1)


def cmd_config(args):
    config = load_config()
    if args.show:
        import json
        print(json.dumps(config, indent=2, ensure_ascii=False))
    elif args.set:
        key_parts = args.key.split(".")
        value = args.value
        # Convert value to appropriate type
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
        # Navigate and set
        target = config
        for part in key_parts[:-1]:
            target = target[part]
        target[key_parts[-1]] = value
        save_config(config)
        print(f"Set {args.key} = {value}")


def main():
    parser = argparse.ArgumentParser(description="Obsidian Vault Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create
    p_create = subparsers.add_parser("create", help="Create a new note")
    p_create.add_argument("name", help="Note name or path")
    p_create.add_argument("--content", help="Note content")
    p_create.add_argument("--open", action="store_true", help="Open in Obsidian after creation")
    p_create.set_defaults(func=cmd_create)

    # edit
    p_edit = subparsers.add_parser("edit", help="Edit an existing note")
    p_edit.add_argument("name", help="Note name or path")
    p_edit.add_argument("--content", required=True, help="Content to write")
    p_edit.add_argument("--append", action="store_true", help="Append instead of overwrite")
    p_edit.set_defaults(func=cmd_edit)

    # fm (frontmatter)
    p_fm = subparsers.add_parser("fm", help="Manage frontmatter")
    p_fm.add_argument("name", help="Note name or path")
    fm_group = p_fm.add_mutually_exclusive_group(required=True)
    fm_group.add_argument("--print", action="store_true", help="Print frontmatter")
    fm_group.add_argument("--set", action="store_true", help="Set a frontmatter field")
    fm_group.add_argument("--delete", action="store_true", help="Delete a frontmatter field")
    p_fm.add_argument("--key", help="Frontmatter key")
    p_fm.add_argument("--value", help="Frontmatter value")
    p_fm.set_defaults(func=cmd_fm)

    # move
    p_move = subparsers.add_parser("move", help="Move or rename a note")
    p_move.add_argument("src", help="Source note path")
    p_move.add_argument("dest", help="Destination note path")
    p_move.add_argument("--open", action="store_true", help="Open after move")
    p_move.set_defaults(func=cmd_move)

    # search
    p_search = subparsers.add_parser("search", help="Search notes")
    search_group = p_search.add_mutually_exclusive_group()
    search_group.add_argument("--name", action="store_true", help="Search by note name (fuzzy)")
    search_group.add_argument("--content", action="store_true", help="Search by note content")
    p_search.add_argument("query", nargs="?", default="", help="Search query")
    p_search.set_defaults(func=cmd_search)

    # list
    p_list = subparsers.add_parser("list", help="List vault contents")
    p_list.add_argument("path", nargs="?", default=None, help="Subdirectory path")
    p_list.set_defaults(func=cmd_list)

    # print
    p_print = subparsers.add_parser("print", help="Print note contents")
    p_print.add_argument("name", help="Note name or path")
    p_print.set_defaults(func=cmd_print)

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a note")
    p_delete.add_argument("name", help="Note name or path")
    p_delete.set_defaults(func=cmd_delete)

    # daily
    p_daily = subparsers.add_parser("daily", help="Create/open daily note")
    p_daily.add_argument("--content", help="Content to add")
    p_daily.set_defaults(func=cmd_daily)

    # attach
    p_attach = subparsers.add_parser("attach", help="Attach a file to the vault")
    p_attach.add_argument("file", help="Path to the file")
    p_attach.add_argument("--name", help="Custom filename in vault")
    p_attach.set_defaults(func=cmd_attach)

    # sync
    p_sync = subparsers.add_parser("sync", help="Sync vault to remote git")
    p_sync.set_defaults(func=cmd_sync)

    # config
    p_config = subparsers.add_parser("config", help="Manage configuration")
    config_group = p_config.add_mutually_exclusive_group()
    config_group.add_argument("--show", action="store_true", help="Display current config")
    config_group.add_argument("--set", action="store_true", help="Set a config value")
    p_config.add_argument("--key", help="Config key (dot notation, e.g. vault.path)")
    p_config.add_argument("--value", help="Config value")
    p_config.set_defaults(func=cmd_config)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify CLI help output**

Run: `python scripts/obsidian_mgr.py --help`
Expected: argparse help with all subcommands listed

Run: `python scripts/obsidian_mgr.py create --help`
Expected: create subcommand help

- [ ] **Step 3: Commit**

```bash
git add scripts/obsidian_mgr.py
git commit -m "feat: add main CLI entry point (argparse router to all modules)"
```

---

### Task 6: Default Config Template

**Files:**
- Create: `obsidian-manager.json`

- [ ] **Step 1: Create `obsidian-manager.json`**

```json
{
  "vault": {
    "path": "",
    "name": ""
  },
  "git": {
    "remote": "",
    "branch": "main",
    "auto_sync_minutes": 30
  },
  "conventions": {
    "attachment_dir": "attachments",
    "daily_dir": "daily",
    "template_dir": "templates",
    "frontmatter": {
      "required_fields": ["title", "tags", "created", "modified"],
      "date_format": "YYYY-MM-DD HH:mm:ss"
    },
    "wikilinks": true
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add obsidian-manager.json
git commit -m "feat: add default config template"
```

---

### Task 7: Main SKILL.md

**Files:**
- Create: `SKILL.md`

- [ ] **Step 1: Create `SKILL.md`**

```markdown
# Obsidian Manager Skill

Manage an Obsidian vault — create, edit, search, and organize notes using `notesmd-cli`, with automated git sync.

## Scheduled Tasks

- `obsidian_sync`: every 30 minutes execute `python scripts/obsidian_mgr.py sync`

## Quick Reference

| Command | Usage |
|---------|-------|
| `create` | `python scripts/obsidian_mgr.py create <name> [--content "..."] [--open]` |
| `edit` | `python scripts/obsidian_mgr.py edit <name> --content "..." [--append]` |
| `fm` | `python scripts/obsidian_mgr.py fm <name> --print \| --set key val \| --delete key` |
| `move` | `python scripts/obsidian_mgr.py move <src> <dest> [--open]` |
| `search` | `python scripts/obsidian_mgr.py search [--name \| --content] <query>` |
| `list` | `python scripts/obsidian_mgr.py list [path]` |
| `print` | `python scripts/obsidian_mgr.py print <name>` |
| `delete` | `python scripts/obsidian_mgr.py delete <name>` |
| `daily` | `python scripts/obsidian_mgr.py daily [--content "..."]` |
| `attach` | `python scripts/obsidian_mgr.py attach <file> [--name "..."]` |
| `sync` | `python scripts/obsidian_mgr.py sync` |
| `config` | `python scripts/obsidian_mgr.py config --show \| --set key val` |

## Documentation

- **First-time setup**: see `docs/01-init.md`
- **Obsidian conventions**: see `docs/02-conventions.md`
- **Full command reference**: see `docs/03-commands.md`
- **Sync mechanism**: see `docs/04-sync.md`
- **Troubleshooting**: see `docs/05-troubleshooting.md`
```

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "feat: add main SKILL.md with quick reference and doc index"
```

---

### Task 8: Documentation Files

**Files:**
- Create: `docs/01-init.md`
- Create: `docs/02-conventions.md`
- Create: `docs/03-commands.md`
- Create: `docs/04-sync.md`
- Create: `docs/05-troubleshooting.md`

- [ ] **Step 1: Create `docs/01-init.md`**

```markdown
# Initialization

## Prerequisites

1. **notesmd-cli**: Install the CLI tool for your platform:
   - Windows (PowerShell):
     ```
     scoop bucket add scoop-yakitrak https://github.com/yakitrak/scoop-yakitrak.git
     scoop install notesmd-cli
     ```
   - macOS / Linux:
     ```
     brew tap yakitrak/yakitrak
     brew install yakitrak/yakitrak/notesmd-cli
     ```

2. **git**: Must be installed and available on PATH.

3. **Obsidian vault**: An existing vault directory on your filesystem.

## Setup

1. Edit `obsidian-manager.json` and set:
   - `vault.path` — absolute path to your Obsidian vault
   - `vault.name` — vault name (use directory name)
   - `git.remote` — remote repository URL (e.g. `https://github.com/user/vault.git`)

   Or use the CLI:
   ```
   python scripts/obsidian_mgr.py config --set vault.path "D:/obsidianDate/my-vault"
   python scripts/obsidian_mgr.py config --set vault.name "my-vault"
   python scripts/obsidian_mgr.py config --set git.remote "https://github.com/user/my-vault.git"
   ```

2. Register the vault with notesmd-cli:
   ```
   notesmd-cli add-vault "D:/obsidianDate/my-vault" --set-default
   ```

3. Initialize git in the vault (auto-done on first sync, or manually):
   ```
   python scripts/obsidian_mgr.py sync
   ```

4. Verify setup:
   ```
   python scripts/obsidian_mgr.py config --show
   python scripts/obsidian_mgr.py list
   ```
```

- [ ] **Step 2: Create `docs/02-conventions.md`**

```markdown
# Obsidian Conventions

## Wikilinks

All internal note references use `[[note-name]]` format. When creating or moving notes, wikilinks are automatically updated by `notesmd-cli`.

## Frontmatter

Every note must have YAML frontmatter with these fields:

```yaml
---
title: Note Title
tags: [tag1, tag2]
created: 2026-07-08 12:00:00
modified: 2026-07-08 12:00:00
---
```

The `create` and `edit` commands auto-inject frontmatter if missing. The `fm` command lets you read/edit/delete individual fields.

Date format is configurable in `obsidian-manager.json` under `conventions.frontmatter.date_format`.

## Directory Structure

| Directory | Purpose | Config Key |
|-----------|---------|------------|
| `attachments/` | Images, PDFs, and other files | `conventions.attachment_dir` |
| `daily/` | Daily notes | `conventions.daily_dir` |
| `templates/` | Note templates | `conventions.template_dir` |

## Attachments

Use `attach` to copy files into the vault. The command copies the file to the configured attachment directory and returns a wikilink reference:

```
> python scripts/obsidian_mgr.py attach "C:/Users/me/photo.png"
[[attachments/photo.png]]
```
```

- [ ] **Step 3: Create `docs/03-commands.md`**

```markdown
# Command Reference

## create — Create a new note

```
python scripts/obsidian_mgr.py create <name> [--content "..."] [--open]
```

- `name`: Note name (with or without `.md` extension, can include subdirectory path)
- `--content`: Initial note content (optional)
- `--open`: Open in Obsidian after creation (optional)

Auto-injects frontmatter with `title`, `tags`, `created`, `modified`.

## edit — Edit an existing note

```
python scripts/obsidian_mgr.py edit <name> --content "..." [--append]
```

- `name`: Note to edit
- `--content`: New content (required)
- `--append`: Append content instead of overwriting

Updates `modified` date in frontmatter.

## fm — Manage frontmatter

```
python scripts/obsidian_mgr.py fm <name> --print
python scripts/obsidian_mgr.py fm <name> --set --key <key> --value <value>
python scripts/obsidian_mgr.py fm <name> --delete --key <key>
```

- `--print`: Display all frontmatter fields
- `--set`: Set or update a field (creates if not exists)
- `--delete`: Remove a field

## move — Move or rename a note

```
python scripts/obsidian_mgr.py move <src> <dest> [--open]
```

Automatically updates all wikilinks across the vault.

## search — Search notes

```
python scripts/obsidian_mgr.py search --name
python scripts/obsidian_mgr.py search --content <query>
```

- `--name`: Interactive fuzzy search by note name
- `--content`: Full-text search in note content (non-interactive)

## list — List vault contents

```
python scripts/obsidian_mgr.py list [path]
```

## print — Print note contents

```
python scripts/obsidian_mgr.py print <name>
```

## delete — Delete a note

```
python scripts/obsidian_mgr.py delete <name>
```

Permanently deletes the file. Use with caution.

## daily — Create or open daily note

```
python scripts/obsidian_mgr.py daily [--content "..."]
```

Respects vault's `.obsidian/daily-notes.json` settings (folder, date format, template).

## attach — Attach a file to the vault

```
python scripts/obsidian_mgr.py attach <file> [--name "..."]
```

Copies file to the configured attachment directory. Returns wikilink.

## sync — Sync vault to remote git

```
python scripts/obsidian_mgr.py sync
```

Pulls remote changes, commits local changes, pushes to remote.

## config — Manage configuration

```
python scripts/obsidian_mgr.py config --show
python scripts/obsidian_mgr.py config --set <key> <value>
```

- `--show`: Print entire config as JSON
- `--set`: Set a config value (dot notation for nested keys, e.g. `git.auto_sync_minutes 15`)
```

- [ ] **Step 4: Create `docs/04-sync.md`**

```markdown
# Git Sync Mechanism

## Trigger

Sync runs as an openclaw scheduled task every 30 minutes (configurable via `git.auto_sync_minutes`).

## Flow

1. Verify vault path exists
2. Initialize git repo if not already (first run only)
3. `git pull --rebase -X theirs origin <branch>` — pull remote changes, resolve conflicts with local
4. `git add -A` — stage all changes
5. Check for staged changes with `git diff --cached --quiet`
6. If changes: `git commit -m "auto: sync <timestamp>"` then `git push origin <branch>`
7. If no changes: skip

## Conflict Resolution

Conflicts are resolved with `-X theirs` during pull, meaning **local changes win**. If both sides modify the same file, the rebase keeps the local version.

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| No network | Push fails, logged to stderr, returns non-zero |
| No changes to sync | Commit/push skipped, returns success |
| Branch doesn't exist on remote | Push creates the branch |
| First run (no .git) | Auto-init + first commit |
| Vault path gone | Error, returns non-zero |

## Manual Sync

```
python scripts/obsidian_mgr.py sync
```

Run anytime to force an immediate sync.
```

- [ ] **Step 5: Create `docs/05-troubleshooting.md`**

```markdown
# Troubleshooting

## Config file not found

```
Config file not found: .../obsidian-manager.json
Run 'python scripts/obsidian_mgr.py init' to set up.
```

Create the config file by copying the default template:
```
# On first run, create from template if needed
python -c "from scripts.config import save_config; import json; save_config(json.load(open('obsidian-manager.json','r',encoding='utf-8')))"
```
Then edit with your vault path and git remote.

## notesmd-cli: command not found

Install notesmd-cli for your platform:
- Windows: `scoop install notesmd-cli`
- macOS/Linux: `brew install yakitrak/yakitrak/notesmd-cli`

Verify: `notesmd-cli --help`

## Vault not registered

If notesmd-cli commands fail with vault-not-found errors:
```
notesmd-cli add-vault "/path/to/vault" --set-default
notesmd-cli list-vaults  # verify it's registered
```

## Git push fails

- Check remote URL: `python scripts/obsidian_mgr.py config --show | grep remote`
- Verify git credentials are configured
- Check network connectivity
- Sync failures do not block note operations

## Python import errors

Run from the project root directory:
```
python scripts/obsidian_mgr.py --help
```

The scripts use relative imports and must be run from the project root.
```

- [ ] **Step 6: Commit**

```bash
git add docs/
git commit -m "feat: add documentation (init, conventions, commands, sync, troubleshooting)"
```

---

### Task 9: Integration Verification

**Files:**
- No new files — verify end-to-end

- [ ] **Step 1: Verify all modules import cleanly**

```bash
python -c "from scripts.config import load_config, save_config, get_config_path; print('config OK')"
python -c "from scripts.conventions import generate_frontmatter, ensure_frontmatter, get_attachment_path, format_wikilink; print('conventions OK')"
python -c "from scripts.sync import run_sync, init_repo; print('sync OK')"
python -c "from scripts.vault import create_note, edit_note, manage_frontmatter, move_note, search_notes, list_vault, print_note, delete_note, daily_note, attach_file; print('vault OK')"
```

Expected: all five modules print "OK"

- [ ] **Step 2: Run all unit tests**

```bash
python -m scripts.test_conventions
python -m scripts.test_sync
python -m scripts.test_vault
```

Expected: all tests pass (6 + 1 + 3 = 10 tests)

- [ ] **Step 3: Test CLI config --show with template**

```bash
python scripts/obsidian_mgr.py config --show
```

Expected: prints the template config JSON (vault.path empty)

- [ ] **Step 4: Test CLI config --set updates a value**

```bash
python scripts/obsidian_mgr.py config --set git.auto_sync_minutes 15
python scripts/obsidian_mgr.py config --show
```

Expected: `auto_sync_minutes` shows `15` instead of `30`

- [ ] **Step 5: Restore original value**

```bash
python scripts/obsidian_mgr.py config --set git.auto_sync_minutes 30
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: final integration verification"
```
```

---

### Task 10: Final Review and Cleanup

- [ ] **Step 1: Verify project structure matches spec**

```bash
git ls-files
```

Expected output:
```
SKILL.md
docs/01-init.md
docs/02-conventions.md
docs/03-commands.md
docs/04-sync.md
docs/05-troubleshooting.md
docs/superpowers/plans/2026-07-08-obsidian-manager-skill-plan.md
docs/superpowers/specs/2026-07-08-obsidian-manager-skill-design.md
obsidian-manager.json
scripts/config.py
scripts/conventions.py
scripts/obsidian_mgr.py
scripts/sync.py
scripts/test_conventions.py
scripts/test_sync.py
scripts/test_vault.py
scripts/vault.py
```

- [ ] **Step 2: Run full test suite one final time**

```bash
python -m scripts.test_conventions; if ($?) { python -m scripts.test_sync }; if ($?) { python -m scripts.test_vault }
```

Expected: all 10 tests pass

- [ ] **Step 3: Commit if any changes**

```bash
git add -A
git diff --cached --quiet; if ($LASTEXITCODE -ne 0) { git commit -m "chore: final review and cleanup" }
```

---

## Phase 2: Knowledge Base System Additions

### Task 11: Extend Conventions Module with Per-Type Frontmatter

**Files:**
- Modify: `scripts/conventions.py`
- Modify: `scripts/test_conventions.py`

**Interfaces:**
- Consumes: existing `generate_frontmatter` (Task 2)
- Produces:
  - `FRONTMATTER_SCHEMAS: dict` — mapping of page type to extra fields
  - `generate_frontmatter_by_type(page_type: str, title: str, tags: list[str], config: dict) -> str`
  - `get_wiki_subdir(page_type: str, config: dict) -> str` — returns subdirectory for page type
  - `get_template_path(page_type: str) -> Path` — returns path to project template file

- [ ] **Step 1: Add schemas and new functions to `scripts/conventions.py`**

Append after existing code:

```python
FRONTMATTER_SCHEMAS = {
    "source": {
        "extra_fields": [
            "source_type", "author", "date_published", "url",
            "confidence", "key_claims",
        ],
        "type": "source",
    },
    "entity": {
        "extra_fields": [
            "entity_type", "role", "first_mentioned",
        ],
        "type": "entity",
    },
    "concept": {
        "extra_fields": [
            "complexity", "domain", "aliases",
        ],
        "type": "concept",
    },
    "comparison": {
        "extra_fields": [
            "subjects", "dimensions", "verdict",
        ],
        "type": "comparison",
    },
    "question": {
        "extra_fields": [
            "question", "answer_quality",
        ],
        "type": "question",
    },
}

UNIVERSAL_FIELDS = ["type", "title", "tags", "created", "modified", "status", "related", "sources"]


def generate_frontmatter_by_type(page_type: str, title: str, tags: list[str], config: dict) -> str:
    schema = FRONTMATTER_SCHEMAS.get(page_type, {})
    fmt = config["conventions"]["frontmatter"]["date_format"]
    now = datetime.now().strftime(fmt)
    lines = ["---"]
    for field in UNIVERSAL_FIELDS:
        if field == "type":
            lines.append(f"type: {schema.get('type', page_type)}")
        elif field == "title":
            lines.append(f"title: {title}")
        elif field == "tags":
            tag_str = ", ".join(tags) if tags else ""
            lines.append(f"tags: [{tag_str}]")
        elif field == "created":
            lines.append(f"created: {now}")
        elif field == "modified":
            lines.append(f"modified: {now}")
        elif field == "status":
            lines.append("status: seed")
        elif field == "related":
            lines.append("related: []")
        elif field == "sources":
            lines.append("sources: []")
    for field in schema.get("extra_fields", []):
        if field == "complexity":
            lines.append("complexity: basic")
        elif field == "aliases":
            lines.append("aliases: []")
        elif field == "entity_type":
            lines.append("entity_type: ")
        elif field == "role":
            lines.append("role: ")
        elif field == "subjects":
            lines.append("subjects: []")
        elif field == "dimensions":
            lines.append("dimensions: []")
        elif field == "verdict":
            lines.append("verdict: ")
        elif field == "confidence":
            lines.append("confidence: medium")
        elif field == "answer_quality":
            lines.append("answer_quality: draft")
        elif field == "key_claims":
            lines.append("key_claims: []")
        else:
            lines.append(f"{field}: ")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def get_wiki_subdir(page_type: str, config: dict) -> str:
    wiki_dir = config.get("knowledge", {}).get("wiki_dir", "wiki")
    subdirs = {
        "concept": "concepts",
        "entity": "entities",
        "source": "sources",
        "comparison": "comparisons",
        "question": "questions",
    }
    sub = subdirs.get(page_type, "")
    if sub:
        return f"{wiki_dir}/{sub}"
    return wiki_dir


def get_template_path(page_type: str) -> Path:
    return Path(__file__).resolve().parent.parent / "_templates" / f"{page_type}.md"
```

- [ ] **Step 2: Add new test cases to `scripts/test_conventions.py`**

Append before `if __name__ == "__main__":`:

```python
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
        self.assertIn("source_type: ", fm)

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
```

**Expected**: 13 tests total (6 original + 7 new)

- [ ] **Step 3: Run all tests and verify pass**

```bash
python -m scripts.test_conventions
```
Expected: 13 tests PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/conventions.py scripts/test_conventions.py
git commit -m "feat: add per-type frontmatter schemas and wiki subdir resolution"
```

---

### Task 12: Create Template Files

**Files:**
- Create: `_templates/concept.md`
- Create: `_templates/entity.md`
- Create: `_templates/source.md`
- Create: `_templates/comparison.md`
- Create: `_templates/question.md`
- Create: `_templates/daily.md`

- [ ] **Step 1: Create `_templates/concept.md`**

```markdown
---
type: concept
title: "{{title}}"
created: {{date}}
updated: {{date}}
tags: []
status: seed
complexity: basic
domain: ""
aliases: []
related: []
sources: []
---

# {{title}}

## Overview

## Key Ideas

## Connections
```

- [ ] **Step 2: Create `_templates/entity.md`**

```markdown
---
type: entity
title: "{{title}}"
created: {{date}}
updated: {{date}}
tags: []
status: seed
entity_type: ""
role: ""
first_mentioned: ""
related: []
sources: []
---

# {{title}}

## Profile

## Role / Significance

## Relationships
```

- [ ] **Step 3: Create `_templates/source.md`**

```markdown
---
type: source
title: "{{title}}"
created: {{date}}
updated: {{date}}
tags: []
status: seed
source_type: ""
author: ""
date_published: ""
url: ""
confidence: medium
key_claims: []
related: []
sources: []
---

# {{title}}

## Summary

## Key Claims

## Notes
```

- [ ] **Step 4: Create `_templates/comparison.md`**

```markdown
---
type: comparison
title: "{{title}}"
created: {{date}}
updated: {{date}}
tags: []
status: seed
subjects: []
dimensions: []
verdict: ""
related: []
sources: []
---

# {{title}}

## Context

## Comparison

| Dimension | A | B |
|-----------|---|---|

## Verdict
```

- [ ] **Step 5: Create `_templates/question.md`**

```markdown
---
type: question
title: "{{title}}"
created: {{date}}
updated: {{date}}
tags: []
status: seed
question: ""
answer_quality: draft
related: []
sources: []
---

# {{title}}

## Question

## Answer

## References
```

- [ ] **Step 6: Create `_templates/daily.md`**

```markdown
---
type: daily
title: "{{title}}"
created: {{date}}
updated: {{date}}
tags: [daily]
---

# {{title}}

## Tasks

- [ ] 

## Notes

## Reflections
```

- [ ] **Step 7: Commit**

```bash
git add _templates/
git commit -m "feat: add note templates for 6 page types"
```

---

### Task 13: Extend Config with Knowledge Section

**Files:**
- Modify: `obsidian-manager.json`

- [ ] **Step 1: Update `obsidian-manager.json`**

Replace current content:

```json
{
  "vault": {
    "path": "",
    "name": ""
  },
  "git": {
    "remote": "",
    "branch": "main",
    "auto_sync_minutes": 30
  },
  "conventions": {
    "attachment_dir": "attachments",
    "daily_dir": "daily",
    "template_dir": "templates",
    "frontmatter": {
      "date_format": "YYYY-MM-DD HH:mm:ss"
    },
    "wikilinks": true
  },
  "knowledge": {
    "wiki_dir": "wiki",
    "raw_dir": ".raw",
    "hot_cache_words": 500,
    "stale_days": 90
  }
}
```

Note: `required_fields` removed from `frontmatter` since we now use per-type schemas.

- [ ] **Step 2: Commit**

```bash
git add obsidian-manager.json
git commit -m "feat: add knowledge config section, remove required_fields from frontmatter"
```

---

### Task 14: Implement Init Vault Script

**Files:**
- Create: `scripts/init_vault.py`

**Interfaces:**
- Consumes: `config.load_config`, `sync.init_repo`
- Produces: `run_init(config: dict) -> None`

- [ ] **Step 1: Create `scripts/init_vault.py`**

```python
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from scripts.config import load_config
from scripts.sync import init_repo


WIKI_DIRS = [
    "concepts",
    "entities",
    "sources",
    "questions",
    "comparisons",
    "domains",
    "meta",
]

OBSIDIAN_APP_JSON = """{
  "newFileLocation": "folder",
  "newFileFolderPath": "wiki",
  "attachmentFolderPath": "attachments",
  "showUnsupportedFiles": false,
  "userIgnoreFilters": [
    ".raw/",
    "_templates/",
    "scripts/",
    ".vault-meta/"
  ]
}
"""

OBSIDIAN_GRAPH_JSON = """{
  "collapse-filter": false,
  "search": "",
  "showTags": true,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": false,
  "colorGroups": [
    {"query": "path:wiki/entities", "color": {"a":1,"rgb":10453373}},
    {"query": "path:wiki/concepts", "color": {"a":1,"rgb":6723867}},
    {"query": "path:wiki/sources", "color": {"a":1,"rgb":16751001}},
    {"query": "path:wiki/questions", "color": {"a":1,"rgb":5292279}},
    {"query": "path:wiki/comparisons", "color": {"a":1,"rgb":13698265}},
    {"query": "path:wiki/domains", "color": {"a":1,"rgb":4360569}},
    {"query": "path:wiki/meta", "color": {"a":1,"rgb":10027263}}
  ],
  "collapse-display": false,
  "showArrow": true,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": false,
  "centerStrength": 0.518713248970312,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250,
  "scale": 1,
  "close": true
}
"""

OBSIDIAN_APPEARANCE_JSON = """{
  "cssTheme": "",
  "baseFontSize": 16,
  "enabledCssSnippets": []
}
"""


def run_init(config: dict) -> None:
    vault_path = Path(config["vault"]["path"])
    wiki_dir = config.get("knowledge", {}).get("wiki_dir", "wiki")
    raw_dir = config.get("knowledge", {}).get("raw_dir", ".raw")

    if not vault_path.exists():
        print(f"Vault path does not exist: {vault_path}", file=sys.stderr)
        print("Create the vault directory first or run:", file=sys.stderr)
        print(f"  python scripts/obsidian_mgr.py config --set vault.path <path>", file=sys.stderr)
        sys.exit(1)

    print(f"Initializing vault at {vault_path}...")

    # 1. Create directory structure
    wiki_path = vault_path / wiki_dir
    raw_path = vault_path / raw_dir
    templates_path = vault_path / "_templates"
    attachments_path = vault_path / config["conventions"]["attachment_dir"]
    obsidian_dir = vault_path / ".obsidian"

    for d in WIKI_DIRS:
        (wiki_path / d).mkdir(parents=True, exist_ok=True)
    raw_path.mkdir(parents=True, exist_ok=True)
    templates_path.mkdir(parents=True, exist_ok=True)
    attachments_path.mkdir(parents=True, exist_ok=True)
    obsidian_dir.mkdir(parents=True, exist_ok=True)
    print("  Created directory structure")

    # 2. Write Obsidian config
    (obsidian_dir / "app.json").write_text(OBSIDIAN_APP_JSON.lstrip(), encoding="utf-8")
    (obsidian_dir / "graph.json").write_text(OBSIDIAN_GRAPH_JSON.lstrip(), encoding="utf-8")
    (obsidian_dir / "appearance.json").write_text(OBSIDIAN_APPEARANCE_JSON.lstrip(), encoding="utf-8")
    print("  Wrote Obsidian configuration")

    # 3. Copy templates from project to vault
    project_templates = Path(__file__).resolve().parent.parent / "_templates"
    if project_templates.exists():
        for tf in project_templates.glob("*.md"):
            dest = templates_path / tf.name
            content = tf.read_text(encoding="utf-8")
            dest.write_text(content, encoding="utf-8")
        print("  Copied templates")

    # 4. Create seed wiki pages
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_only = datetime.now().strftime("%Y-%m-%d")

    _index_content = """---
type: index
title: "{title}"
created: {now}
updated: {now}
tags: []
---

# {title}

Index of {title_lower} pages.
"""

    for wd in WIKI_DIRS:
        title = wd.capitalize()
        (wiki_path / wd / "_index.md").write_text(
            _index_content.format(title=title, now=now, title_lower=wd),
            encoding="utf-8",
        )

    (wiki_path / "index.md").write_text(f"""---
type: index
title: "Vault Index"
created: {now}
updated: {now}
tags: [meta]
---

# Vault Index

## Concepts

## Entities

## Sources

## Questions

## Comparisons

## Domains

## Meta
""", encoding="utf-8")

    (wiki_path / "hot.md").write_text(f"""---
type: meta
title: "Hot Cache"
created: {now}
updated: {now}
tags: [meta]
---

# Hot Cache

## Last Updated
{date_only}

## Key Recent Facts

## Recent Changes

## Active Threads
""", encoding="utf-8")

    (wiki_path / "log.md").write_text(f"""---
type: meta
title: "Operation Log"
created: {now}
updated: {now}
tags: [meta]
---

# Operation Log

## {now} — Vault initialized
""", encoding="utf-8")

    (wiki_path / "overview.md").write_text(f"""---
type: overview
title: "Vault Overview"
created: {now}
updated: {now}
tags: [meta]
---

# Vault Overview

This vault is managed by openclaw-obsidian-manager.

## Structure

- **wiki/** — Knowledge base
- **.raw/** — Immutable source documents
- **_templates/** — Note templates
- **attachments/** — Images and files
""", encoding="utf-8")

    print("  Created seed wiki pages")

    # 5. Initialize git
    remote = config["git"]["remote"]
    branch = config["git"]["branch"]
    if remote:
        init_repo(vault_path, remote, branch)
        print("  Initialized git repository")

    # 6. Register vault with notesmd-cli
    result = subprocess.run(
        ["notesmd-cli", "add-vault", str(vault_path), "--set-default"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  Warning: Could not register vault with notesmd-cli: {result.stderr.strip()}")
    else:
        print("  Registered vault with notesmd-cli")

    print(f"\nVault initialized: {vault_path}")
    print("Next steps:")
    print("  - Open the vault in Obsidian")
    print("  - Start creating notes with: python scripts/obsidian_mgr.py create <name> --type concept")
```

- [ ] **Step 2: Write test `scripts/test_init_vault.py`**

```python
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.init_vault import WIKI_DIRS


class TestInitVault(unittest.TestCase):
    def setUp(self):
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
```

- [ ] **Step 3: Run tests**

```bash
python -m scripts.test_init_vault
```
Expected: 2 tests PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/init_vault.py scripts/test_init_vault.py
git commit -m "feat: add init_vault.py (directory scaffold, Obsidian config, templates, seed pages, git init)"
```

---

### Task 15: Implement Lint Script

**Files:**
- Create: `scripts/lint.py`

**Interfaces:**
- Consumes: `config.load_config`
- Produces: `run_lint(config: dict, fix: bool = False) -> dict`

- [ ] **Step 1: Create `scripts/lint.py`**

```python
import sys
from datetime import datetime, timedelta
from pathlib import Path

from scripts.config import load_config


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm_lines = parts[1].strip().split("\n")
    body = parts[2].strip()
    fm = {}
    for line in fm_lines:
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, body


def _find_wikilinks(content: str) -> list[str]:
    import re
    links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
    return [link.split("#")[0].split("|")[0].strip() for link in links]


def run_lint(config: dict, fix: bool = False) -> dict:
    vault_path = Path(config["vault"]["path"])
    wiki_dir = config.get("knowledge", {}).get("wiki_dir", "wiki")
    stale_days = config.get("knowledge", {}).get("stale_days", 90)
    wiki_path = vault_path / wiki_dir

    if not wiki_path.exists():
        print(f"Wiki directory not found: {wiki_path}", file=sys.stderr)
        return {"error": "wiki directory not found"}

    issues = {
        "orphans": [],
        "dead_links": [],
        "stale": [],
        "missing_fm": [],
        "type_mismatch": [],
        "empty_pages": [],
        "index_stale": [],
        "ambiguous_names": [],
    }

    all_pages = {}       # name -> full path
    all_names = {}       # name -> list of paths (for ambiguity detection)
    page_fm = {}         # path -> frontmatter dict
    page_bodies = {}     # path -> body text
    note_files = []      # list of (name, path)

    for md_file in wiki_path.rglob("*.md"):
        if ".obsidian" in str(md_file) or ".git" in str(md_file.parts):
            continue
        name = md_file.stem
        all_pages[name] = md_file
        if name not in all_names:
            all_names[name] = []
        all_names[name].append(md_file)
        content = md_file.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(content)
        page_fm[str(md_file)] = fm
        page_bodies[str(md_file)] = body
        note_files.append((name, md_file))

    # 1. Ambiguous names
    for name, paths in all_names.items():
        if len(paths) > 1:
            issues["ambiguous_names"].append(
                f"Name '{name}' found in {len(paths)} locations: " +
                ", ".join(str(p.relative_to(vault_path)) for p in paths)
            )

    # 2. Missing frontmatter
    for name, path in note_files:
        fm = page_fm[str(path)]
        required = ["type", "title", "created", "updated"]
        missing = [f for f in required if f not in fm]
        if missing:
            issues["missing_fm"].append(
                f"{path.relative_to(vault_path)} — missing: {', '.join(missing)}"
            )

    # 3. Type mismatch (type vs directory)
    type_to_dir = {
        "concept": "concepts",
        "entity": "entities",
        "source": "sources",
        "question": "questions",
        "comparison": "comparisons",
    }
    for name, path in note_files:
        fm = page_fm[str(path)]
        page_type = fm.get("type", "")
        if page_type in type_to_dir:
            expected_dir_name = type_to_dir[page_type]
            if wiki_dir:
                expected_rel = f"{wiki_dir}/{expected_dir_name}"
            else:
                expected_rel = expected_dir_name
            parent_name = path.parent.name
            if parent_name != expected_dir_name and parent_name != wiki_dir:
                issues["type_mismatch"].append(
                    f"{path.relative_to(vault_path)} — type={page_type} but in dir '{parent_name}'"
                )

    # 4. Empty pages (frontmatter only, no body)
    for name, path in note_files:
        body = page_bodies[str(path)]
        if not body:
            issues["empty_pages"].append(
                f"{path.relative_to(vault_path)}"
            )

    # 5. Dead links
    all_referenced = set()
    for name, path in note_files:
        full_content = path.read_text(encoding="utf-8")
        links = _find_wikilinks(full_content)
        for link in links:
            all_referenced.add(link)
            cleaned = link.split("/")[-1] if "/" in link else link
            if cleaned not in all_pages:
                issues["dead_links"].append(
                    f"{path.relative_to(vault_path)} → [[{link}]] (not found)"
                )

    # 6. Orphan pages (no incoming wikilinks)
    for name, path in note_files:
        ref_key = str(path.relative_to(wiki_path))
        is_referenced = name in all_referenced or ref_key in all_referenced
        fm = page_fm[str(path)]
        if not is_referenced and name not in ["index", "hot", "log", "overview", "_index"]:
            if fm.get("type") not in ["index", "meta", "overview"]:
                issues["orphans"].append(
                    f"{path.relative_to(vault_path)} — no incoming links"
                )

    # 7. Stale content
    now = datetime.now()
    stale_threshold = now - timedelta(days=stale_days)
    for name, path in note_files:
        fm = page_fm[str(path)]
        updated_str = fm.get("updated", "")
        try:
            updated = datetime.strptime(updated_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            try:
                updated = datetime.strptime(updated_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                continue
        status = fm.get("status", "")
        if status in ("mature", "evergreen") and updated < stale_threshold:
            issues["stale"].append(
                f"{path.relative_to(vault_path)} — last updated {updated_str}"
            )

    # 8. Index stale (index references deleted pages)
    index_path = wiki_path / "index.md"
    if index_path.exists():
        index_content = index_path.read_text(encoding="utf-8")
        index_links = _find_wikilinks(index_content)
        for link in index_links:
            if link not in all_pages:
                issues["index_stale"].append(
                    f"index.md → [[{link}]] (page not found)"
                )

    # Print report
    total = sum(len(v) for v in issues.values())
    print(f"Lint Report — {total} issue(s) found\n")

    labels = {
        "orphans": "Orphan Pages (no incoming links)",
        "dead_links": "Dead Links",
        "stale": "Stale Content",
        "missing_fm": "Missing Frontmatter",
        "type_mismatch": "Type Mismatch",
        "empty_pages": "Empty Pages",
        "index_stale": "Stale Index Entries",
        "ambiguous_names": "Ambiguous Names",
    }

    for key, label in labels.items():
        items = issues[key]
        if items:
            print(f"## {label} ({len(items)})")
            for item in items:
                print(f"  - {item}")
            print()

    if total == 0:
        print("All clear!")

    meta_dir = wiki_path / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    report_path = meta_dir / "lint-report.md"
    report = [f"# Lint Report — {now.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    report.append(f"Total issues: {total}\n")
    for key, label in labels.items():
        items = issues[key]
        if items:
            report.append(f"## {label} ({len(items)})")
            for item in items:
                report.append(f"- {item}")
            report.append("")
    if total == 0:
        report.append("All clear!")
    report_path.write_text("\n".join(report), encoding="utf-8")
    print(f"\nReport saved to {report_path.relative_to(vault_path)}")

    return issues
```

- [ ] **Step 2: Write test `scripts/test_lint.py`**

```python
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
```

- [ ] **Step 3: Run tests and verify**

```bash
python -m scripts.test_lint
```
Expected: 4 tests PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/lint.py scripts/test_lint.py
git commit -m "feat: add lint.py (8-category vault health check)"
```

---

### Task 16: Add --type Support to Vault and CLI Integration

**Files:**
- Modify: `scripts/vault.py` — add `type` parameter to `create_note`
- Modify: `scripts/obsidian_mgr.py` — add `init`, `lint`, `--type` to create

- [ ] **Step 1: Modify `create_note` in `scripts/vault.py`**

Replace the existing `create_note` function:

```python
def create_note(config: dict, name: str, content: str = None, open_note: bool = False, page_type: str = None) -> None:
    vault_name = _get_vault_name(config)
    vault_path = Path(config["vault"]["path"])

    if page_type:
        from scripts.conventions import get_wiki_subdir, get_template_path, generate_frontmatter_by_type
        subdir = get_wiki_subdir(page_type, config)
        dest_dir = vault_path / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        target_name = name
        if not target_name.endswith(".md"):
            target_name = name + ".md"
        note_path = dest_dir / target_name

        template_path = get_template_path(page_type)
        if template_path.exists():
            template_content = template_path.read_text(encoding="utf-8")
            from datetime import datetime
            now = datetime.now().strftime(config["conventions"]["frontmatter"]["date_format"])
            date_only = datetime.now().strftime("%Y-%m-%d")
            text = template_content.replace("{{title}}", name).replace("{{date}}", date_only)
            if content:
                text += "\n" + content
        else:
            fm = generate_frontmatter_by_type(page_type, name, [], config)
            text = fm + (content or "")

        note_path.write_text(text, encoding="utf-8")

        if open_note:
            _run_notesmd(["open", str(note_path.relative_to(vault_path)), "--vault", vault_name])
        print(f"Created: {note_path.relative_to(vault_path)}")
        return

    note_path = _get_note_path(config, name)
    args = ["create", name, "--vault", vault_name]
    if content:
        args.extend(["--content", content])
    if open_note:
        args.append("--open")

    result = _run_notesmd(args)
    if result.returncode != 0:
        print(f"Create failed: {result.stderr.strip()}", file=sys.stderr)
        return

    print(result.stdout.strip())

    if note_path.exists():
        ensure_frontmatter(note_path, config)
        _update_frontmatter_date(note_path, config)
```

- [ ] **Step 2: Add init/lint/--type to `scripts/obsidian_mgr.py`**

Add imports after existing ones:

```python
from scripts.init_vault import run_init
from scripts.lint import run_lint
```

Update `cmd_create`:

```python
def cmd_create(args):
    config = load_config()
    create_note(config, args.name, args.content, args.open, args.type)
```

Update `p_create` to add `--type`:

```python
    p_create = subparsers.add_parser("create", help="Create a new note")
    p_create.add_argument("name", help="Note name or path")
    p_create.add_argument("--content", help="Note content")
    p_create.add_argument("--open", action="store_true", help="Open in Obsidian after creation")
    p_create.add_argument("--type", choices=["concept","entity","source","comparison","question"],
                          help="Note type (uses template and wiki subdirectory)")
    p_create.set_defaults(func=cmd_create)
```

Add `init` and `lint` subcommands before `args = parser.parse_args()`:

```python
    p_init = subparsers.add_parser("init", help="Initialize vault structure")
    p_init.set_defaults(func=cmd_init)

    p_lint = subparsers.add_parser("lint", help="Run vault health check")
    p_lint.add_argument("--fix", action="store_true", help="Auto-fix issues")
    p_lint.set_defaults(func=cmd_lint)
```

Add handler functions:

```python
def cmd_init(args):
    config = load_config()
    run_init(config)


def cmd_lint(args):
    config = load_config()
    run_lint(config, args.fix)
```

- [ ] **Step 3: Verify CLI help shows new commands**

```bash
python scripts/obsidian_mgr.py --help
```
Expected: `init` and `lint` listed, `create` shows `--type` option

- [ ] **Step 4: Run all existing tests**

```bash
python -m scripts.test_conventions; python -m scripts.test_sync; python -m scripts.test_vault; python -m scripts.test_init_vault; python -m scripts.test_lint
```
Expected: all tests pass (13 + 1 + 3 + 2 + 4 = 23 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/vault.py scripts/obsidian_mgr.py
git commit -m "feat: add --type support to create, init and lint CLI commands"
```

---

### Task 17: Update Documentation

**Files:**
- Create: `docs/06-knowledge-structure.md`
- Modify: `docs/02-conventions.md`

- [ ] **Step 1: Create `docs/06-knowledge-structure.md`**

```markdown
# Knowledge Base Structure

## Directory Layout

```
wiki/
├── index.md            # Master catalog: all pages by type with one-line summaries
├── hot.md              # Hot cache: ~500-word recent context summary
├── log.md              # Append-only operation log (newest at top)
├── overview.md         # Vault summary
├── concepts/           # Ideas, patterns, frameworks (+ _index.md)
├── entities/           # People, orgs, products, repositories (+ _index.md)
├── sources/            # Source document summaries (+ _index.md)
├── questions/          # Filed answers (+ _index.md)
├── comparisons/        # Side-by-side analyses (+ _index.md)
├── domains/            # Top-level topic areas (+ _index.md)
└── meta/               # Dashboards, lint reports (+ _index.md)
```

## Page Types

### concept — Ideas, patterns, frameworks

```yaml
type: concept
complexity: basic | intermediate | advanced
domain: ""
aliases: []
```

### entity — People, organizations, products

```yaml
type: entity
entity_type: person | organization | product | repository
role: ""
first_mentioned: ""
```

### source — Source document summaries

```yaml
type: source
source_type: article | book | video | podcast | paper
author: ""
date_published: ""
url: ""
confidence: high | medium | low
key_claims: []
```

### comparison — Side-by-side analyses

```yaml
type: comparison
subjects: []
dimensions: []
verdict: ""
```

### question — Filed answers

```yaml
type: question
question: ""
answer_quality: draft | solid | definitive
```

## Status Lifecycle

```
seed → developing → mature → evergreen
```

- **seed**: New page, minimal content
- **developing**: Actively being expanded
- **mature**: Comprehensive, stable
- **evergreen**: Requires minimal updates

## Workflows

### Create with type

```
python scripts/obsidian_mgr.py create "Machine Learning" --type concept
```

Creates the note in `wiki/concepts/`, uses `_templates/concept.md`, injects per-type frontmatter.

### Lint

```
python scripts/obsidian_mgr.py lint
```

Checks 8 categories: orphans, dead links, stale content, missing frontmatter, type mismatches, empty pages, stale index entries, ambiguous names.
```

- [ ] **Step 2: Update `docs/02-conventions.md`**

Replace the frontmatter section with:

```markdown
# Obsidian Conventions

## Wikilinks

All internal note references use `[[note-name]]` format. When creating or moving notes, wikilinks are automatically updated by `notesmd-cli`.

## Frontmatter

Every wiki note must have YAML frontmatter. Two levels of schema:

**Universal fields (all pages):**

```yaml
---
type: <concept|entity|source|comparison|question>
title: "Page Title"
created: 2026-07-08
updated: 2026-07-08
tags: [tag1, tag2]
status: seed | developing | mature | evergreen
related: ["[[Page A]]"]
sources: ["[[.raw/source.md]]"]
---
```

**Type-specific fields** are injected automatically when using `create --type`. See `docs/06-knowledge-structure.md` for full schema details.

The `create` and `edit` commands auto-inject frontmatter. The `fm` command lets you read/edit/delete individual fields.

Date format is configurable in `obsidian-manager.json` under `conventions.frontmatter.date_format`.

## Directory Structure

| Directory | Purpose | Config Key |
|-----------|---------|------------|
| `attachments/` | Images, PDFs, and other files | `conventions.attachment_dir` |
| `daily/` | Daily notes | `conventions.daily_dir` |
| `_templates/` | Note templates | `conventions.template_dir` |
| `wiki/` | Knowledge base | `knowledge.wiki_dir` |
| `.raw/` | Immutable source documents | `knowledge.raw_dir` |

## Attachments

Use `attach` to copy files into the vault. The command copies the file to the configured attachment directory and returns a wikilink reference:

```
> python scripts/obsidian_mgr.py attach "C:/Users/me/photo.png"
[[attachments/photo.png]]
```
```

- [ ] **Step 3: Update `docs/01-init.md`**

Replace with:

```markdown
# Initialization

## Prerequisites

1. **notesmd-cli**: Install the CLI tool for your platform:
   - Windows (PowerShell):
     ```
     scoop bucket add scoop-yakitrak https://github.com/yakitrak/scoop-yakitrak.git
     scoop install notesmd-cli
     ```
   - macOS / Linux:
     ```
     brew tap yakitrak/yakitrak
     brew install yakitrak/yakitrak/notesmd-cli
     ```

2. **git**: Must be installed and available on PATH.

3. **Obsidian vault**: Create an empty directory for your vault.

## One-Click Setup

```
python scripts/obsidian_mgr.py config --set vault.path "D:/obsidianDate/my-vault"
python scripts/obsidian_mgr.py config --set vault.name "my-vault"
python scripts/obsidian_mgr.py config --set git.remote "https://github.com/user/my-vault.git"
python scripts/obsidian_mgr.py init
```

This performs:
1. Creates `wiki/` directory structure (concepts, entities, sources, etc.)
2. Writes Obsidian configuration (app.json, graph.json, appearance.json)
3. Copies templates from project to vault's `_templates/`
4. Creates seed wiki pages (index.md, hot.md, log.md, overview.md)
5. Initializes git repository
6. Registers vault with notesmd-cli

## Verify Setup

```
python scripts/obsidian_mgr.py config --show
python scripts/obsidian_mgr.py list
```
```

- [ ] **Step 4: Commit**

```bash
git add docs/
git commit -m "docs: add knowledge-structure guide, update conventions and init docs"
```

---

### Task 18: Update SKILL.md

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: Update `SKILL.md`**

Replace current content:

```markdown
# Obsidian Manager Skill

Manage an Obsidian vault -- create, edit, search, and organize notes using `notesmd-cli`, with automated git sync, knowledge base structure, and health checks.

## Scheduled Tasks

- `obsidian_sync`: every 30 minutes execute `python scripts/obsidian_mgr.py sync`

## Quick Reference

### Setup
| Command | Usage |
|---------|-------|
| `init` | `python scripts/obsidian_mgr.py init` |

### Notes
| Command | Usage |
|---------|-------|
| `create` | `python scripts/obsidian_mgr.py create <name> [--content "..."] [--type concept|entity|source|comparison|question] [--open]` |
| `edit` | `python scripts/obsidian_mgr.py edit <name> --content "..." [--append]` |
| `move` | `python scripts/obsidian_mgr.py move <src> <dest> [--open]` |
| `delete` | `python scripts/obsidian_mgr.py delete <name>` |
| `print` | `python scripts/obsidian_mgr.py print <name>` |
| `daily` | `python scripts/obsidian_mgr.py daily [--content "..."]` |

### Frontmatter
| Command | Usage |
|---------|-------|
| `fm` | `python scripts/obsidian_mgr.py fm <name> --print \| --set key val \| --delete key` |

### Search & Browse
| Command | Usage |
|---------|-------|
| `search` | `python scripts/obsidian_mgr.py search [--name \| --content] <query>` |
| `list` | `python scripts/obsidian_mgr.py list [path]` |

### Files
| Command | Usage |
|---------|-------|
| `attach` | `python scripts/obsidian_mgr.py attach <file> [--name "..."]` |

### Maintenance
| Command | Usage |
|---------|-------|
| `sync` | `python scripts/obsidian_mgr.py sync` |
| `lint` | `python scripts/obsidian_mgr.py lint [--fix]` |
| `config` | `python scripts/obsidian_mgr.py config --show \| --set key val` |

## Documentation

- **First-time setup**: see `docs/01-init.md`
- **Obsidian conventions**: see `docs/02-conventions.md`
- **Full command reference**: see `docs/03-commands.md`
- **Sync mechanism**: see `docs/04-sync.md`
- **Troubleshooting**: see `docs/05-troubleshooting.md`
- **Knowledge base structure**: see `docs/06-knowledge-structure.md`
```

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "docs: update SKILL.md with new init/lint commands and --type option"
```

---

### Task 19: Integration Test

**Files:**
- No new files — verify end-to-end

- [ ] **Step 1: Run all tests**

```bash
python -m scripts.test_conventions; python -m scripts.test_sync; python -m scripts.test_vault; python -m scripts.test_init_vault; python -m scripts.test_lint
```
Expected: all 23 tests pass

- [ ] **Step 2: Verify CLI help is complete**

```bash
python scripts/obsidian_mgr.py --help
python scripts/obsidian_mgr.py init --help
python scripts/obsidian_mgr.py lint --help
python scripts/obsidian_mgr.py create --help
```
Expected: all subcommands show correct help

- [ ] **Step 3: Test init on a temp vault**

```bash
python scripts/obsidian_mgr.py config --set vault.path "C:\Users\21920\AppData\Local\Temp\test-vault"
python scripts/obsidian_mgr.py init
```
Expected: creates full structure, no errors

- [ ] **Step 4: Test create --type**

```bash
python scripts/obsidian_mgr.py create "Test Concept" --type concept
python scripts/obsidian_mgr.py create "Test Entity" --type entity
python scripts/obsidian_mgr.py print "Test Concept"
python scripts/obsidian_mgr.py print "Test Entity"
```
Expected: notes created in correct subdirectories with correct frontmatter

- [ ] **Step 5: Test lint**

```bash
python scripts/obsidian_mgr.py lint
```
Expected: report with few/no issues

- [ ] **Step 6: Clean up test vault and restore config**

```bash
python scripts/obsidian_mgr.py config --set vault.path ""
Remove-Item -Recurse -Force "C:\Users\21920\AppData\Local\Temp\test-vault"
```

- [ ] **Step 7: Commit if any changes**

```bash
git add -A
git diff --cached --quiet; if ($LASTEXITCODE -ne 0) { git commit -m "chore: integration test fixes" }
```
