import shutil
import subprocess
import sys
from datetime import datetime
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

    if note_path.exists():
        ensure_frontmatter(note_path, config)
        _update_frontmatter_date(note_path, config)


def edit_note(config: dict, name: str, content: str, append: bool = False) -> None:
    vault_name = _get_vault_name(config)
    note_path = _get_note_path(config, name)

    if not note_path.exists():
        print(f"Note not found: {name}", file=sys.stderr)
        return

    if append:
        existing = note_path.read_text(encoding="utf-8")
        note_path.write_text(existing + "\n" + content, encoding="utf-8")
    else:
        args = ["create", name, "--vault", vault_name, "--content", content, "--overwrite"]
        result = _run_notesmd(args)
        if result.returncode != 0:
            print(f"Edit failed: {result.stderr.strip()}", file=sys.stderr)
            return

    ensure_frontmatter(note_path, config)
    _update_frontmatter_date(note_path, config)
    print(f"Updated: {name}")


def _update_frontmatter_date(note_path: Path, config: dict) -> None:
    content = note_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return
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

    vault_path = Path(config["vault"]["path"])
    daily_dir = config["conventions"]["daily_dir"]
    daily_path = vault_path / daily_dir
    if daily_path.exists():
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
