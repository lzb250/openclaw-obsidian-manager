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
