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
