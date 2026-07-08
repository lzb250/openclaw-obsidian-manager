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

    all_pages = {}
    all_names = {}
    page_fm = {}
    page_bodies = {}
    note_files = []

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

    for name, paths in all_names.items():
        if name == "_index":
            continue
        if len(paths) > 1:
            issues["ambiguous_names"].append(
                f"Name '{name}' found in {len(paths)} locations: " +
                ", ".join(str(p.relative_to(vault_path)) for p in paths)
            )

    for name, path in note_files:
        fm = page_fm[str(path)]
        required = ["type", "title", "created", "updated"]
        missing = [f for f in required if f not in fm]
        if missing:
            issues["missing_fm"].append(
                f"{path.relative_to(vault_path)} — missing: {', '.join(missing)}"
            )

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
            parent_name = path.parent.name
            if parent_name != expected_dir_name and parent_name != wiki_dir:
                issues["type_mismatch"].append(
                    f"{path.relative_to(vault_path)} — type={page_type} but in dir '{parent_name}'"
                )

    for name, path in note_files:
        body = page_bodies[str(path)]
        if not body:
            issues["empty_pages"].append(
                f"{path.relative_to(vault_path)}"
            )

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

    for name, path in note_files:
        is_referenced = name in all_referenced
        fm = page_fm[str(path)]
        if not is_referenced and name not in ["index", "hot", "log", "overview", "_index"]:
            if fm.get("type") not in ["index", "meta", "overview"]:
                issues["orphans"].append(
                    f"{path.relative_to(vault_path)} — no incoming links"
                )

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

    index_path = wiki_path / "index.md"
    if index_path.exists():
        index_content = index_path.read_text(encoding="utf-8")
        index_links = _find_wikilinks(index_content)
        for link in index_links:
            if link not in all_pages:
                issues["index_stale"].append(
                    f"index.md → [[{link}]] (page not found)"
                )

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
