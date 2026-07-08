from datetime import datetime
from pathlib import Path

from scripts.config import load_config


def generate_frontmatter(title: str, tags: list[str], config: dict) -> str:
    fmt = config["conventions"]["frontmatter"]["date_format"]
    now = datetime.now().strftime(fmt)
    fields = config["conventions"]["frontmatter"].get(
        "required_fields", ["title", "tags", "created", "modified"]
    )
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

_DEFAULT_VALUES = {
    "complexity": "basic",
    "aliases": "[]",
    "entity_type": "",
    "role": "",
    "subjects": "[]",
    "dimensions": "[]",
    "verdict": "",
    "confidence": "medium",
    "answer_quality": "draft",
    "key_claims": "[]",
    "source_type": "",
    "author": "",
    "date_published": "",
    "url": "",
    "first_mentioned": "",
    "question": "",
    "domain": "",
}


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
        default = _DEFAULT_VALUES.get(field, "")
        lines.append(f"{field}: {default}")
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
