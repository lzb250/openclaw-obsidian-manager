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
    generate_frontmatter_by_type,
    get_attachment_path,
    get_wiki_subdir,
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


def _parse_fm_lines(content: str) -> tuple[list[str], str, int]:
    """Return (frontmatter lines, body text, closing --- index)."""
    if not content.startswith("---"):
        return [], content, 0
    lines = content.split("\n")
    end = 1
    while end < len(lines) and lines[end].strip() != "---":
        end += 1
    fm_lines = lines[1:end]
    body = "\n".join(lines[end + 1:])
    return fm_lines, body, end


def _write_fm_and_body(fm_lines: list[str], body: str) -> str:
    return "---\n" + "\n".join(fm_lines) + "\n---\n\n" + body.lstrip("\n")


def _add_backlink(target_path: Path, new_wikilink: str) -> None:
    """Add [[new_wikilink]] to target page's related field."""
    if not target_path.exists():
        return
    content = target_path.read_text(encoding="utf-8")
    fm_lines, body, _ = _parse_fm_lines(content)
    quoted = '"' + new_wikilink + '"'
    for i, line in enumerate(fm_lines):
        if line.strip().startswith("related:"):
            val = line.split(":", 1)[1].strip()
            if val == "[]":
                fm_lines[i] = f"related: [{quoted}]"
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                if not inner:
                    fm_lines[i] = f"related: [{quoted}]"
                else:
                    fm_lines[i] = f"related: [{inner}, {quoted}]"
            else:
                fm_lines[i] = f"related: [{val}, {quoted}]"
            break
    target_path.write_text(_write_fm_and_body(fm_lines, body), encoding="utf-8")


def _ensure_domain_page(config: dict, domain_name: str) -> Path:
    """Create domain page if missing, return its path."""
    vault_path = Path(config["vault"]["path"])
    wiki_dir = config.get("knowledge", {}).get("wiki_dir", "wiki")
    domains_dir = vault_path / wiki_dir / "domains"
    domains_dir.mkdir(parents=True, exist_ok=True)
    domain_path = domains_dir / f"{domain_name}.md"

    if not domain_path.exists():
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_only = datetime.now().strftime("%Y-%m-%d")
        domain_path.write_text(f"""---
type: domain
title: "{domain_name}"
created: {now}
updated: {now}
tags: []
status: seed
related: []
sources: []
---

# {domain_name}

## Overview

## Subtopics

## Related Pages
""", encoding="utf-8")
        print(f"  Created domain page: {domain_path.relative_to(vault_path)}")
    return domain_path


def _update_index(config: dict, note_wikilink: str, page_type: str, summary: str) -> None:
    """Add an entry to wiki/index.md under the appropriate type section."""
    vault_path = Path(config["vault"]["path"])
    wiki_dir = config.get("knowledge", {}).get("wiki_dir", "wiki")
    index_path = vault_path / wiki_dir / "index.md"
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")
    type_headers = {
        "concept": "## Concepts",
        "entity": "## Entities",
        "source": "## Sources",
        "question": "## Questions",
        "comparison": "## Comparisons",
        "domain": "## Domains",
    }
    header = type_headers.get(page_type, f"## {page_type.capitalize()}s")
    entry = f"- {note_wikilink} — {summary}"

    lines = content.split("\n")
    in_section = False
    insert_at = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            in_section = True
        elif in_section and line.strip().startswith("## "):
            insert_at = i
            break
        elif in_section:
            if line.strip() == entry:
                return  # already exists
    if insert_at is None and in_section:
        insert_at = len(lines)

    if insert_at is not None:
        lines.insert(insert_at, entry)
        index_path.write_text("\n".join(lines), encoding="utf-8")


def _update_subdir_index(config: dict, note_wikilink: str, page_type: str, summary: str) -> None:
    """Add an entry to wiki/<subdir>/_index.md."""
    vault_path = Path(config["vault"]["path"])
    wiki_dir = config.get("knowledge", {}).get("wiki_dir", "wiki")
    subdir = get_wiki_subdir(page_type, config)
    index_path = vault_path / subdir / "_index.md"
    if not index_path.exists():
        return

    entry = f"- {note_wikilink}"
    content = index_path.read_text(encoding="utf-8")
    if entry in content:
        return

    with open(index_path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def _resolve_wikilink_path(config: dict, wikilink: str) -> Path:
    """Resolve [[Page Name]] or [[subdir/Page Name]] to an absolute file path."""
    vault_path = Path(config["vault"]["path"])
    name = wikilink.strip("[]").strip()
    if "/" in name:
        candidate = vault_path / (name + ".md" if not name.endswith(".md") else name)
    else:
        wiki_dir = config.get("knowledge", {}).get("wiki_dir", "wiki")
        for root, dirs, files in os.walk(vault_path / wiki_dir):
            for f in files:
                if f == f"{name}.md" or f == name:
                    return Path(root) / f
        candidate = vault_path / (name + ".md" if not name.endswith(".md") else name)
    return candidate if candidate.exists() else None


import os


def create_note(config: dict, name: str, content: str = None, open_note: bool = False,
                page_type: str = None, domain: str = None, related: list[str] = None) -> None:
    vault_name = _get_vault_name(config)
    vault_path = Path(config["vault"]["path"])

    if page_type:
        subdir = get_wiki_subdir(page_type, config)
        dest_dir = vault_path / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        target_name = name if name.endswith(".md") else name + ".md"
        note_path = dest_dir / target_name

        template_path = Path(__file__).resolve().parent.parent / "_templates" / f"{page_type}.md"
        if template_path.exists():
            template_content = template_path.read_text(encoding="utf-8")
            date_only = datetime.now().strftime("%Y-%m-%d")
            text = template_content.replace("{{title}}", name).replace("{{date}}", date_only)
        else:
            fm = generate_frontmatter_by_type(page_type, name, [], config)
            text = fm

        # Inject domain and related into frontmatter
        rel_list = []
        if domain:
            rel_list.append(f"[[{domain}]]")
        if related:
            rel_list.extend(related)
        if rel_list:
            fm_lines, body, _ = _parse_fm_lines(text)
            entries = ", ".join(f'"{r}"' for r in rel_list)
            for i, line in enumerate(fm_lines):
                if line.strip().startswith("related:"):
                    fm_lines[i] = f"related: [{entries}]"
                    break
            text = _write_fm_and_body(fm_lines, body)

        if content:
            text += "\n" + content

        note_path.write_text(text, encoding="utf-8")
        note_rel = str(note_path.relative_to(vault_path)).replace("\\", "/")
        note_wikilink = f"[[{note_rel}]]"

        # 1. Handle domain: create domain page, add backlinks
        if domain:
            domain_path = _ensure_domain_page(config, domain)
            _add_backlink(domain_path, note_wikilink)

        # 2. Handle related: add backlinks to target pages
        if related:
            for rel in related:
                target_path = _resolve_wikilink_path(config, rel)
                if target_path:
                    _add_backlink(target_path, note_wikilink)

        # 3. Update indexes
        _update_index(config, note_wikilink, page_type, name)
        _update_subdir_index(config, note_wikilink, page_type, name)

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
