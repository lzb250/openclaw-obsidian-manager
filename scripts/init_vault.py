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
        print(f"Creating vault directory: {vault_path}")
        vault_path.mkdir(parents=True, exist_ok=True)

    print(f"Initializing vault at {vault_path}...")

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

    (obsidian_dir / "app.json").write_text(OBSIDIAN_APP_JSON.lstrip(), encoding="utf-8")
    (obsidian_dir / "graph.json").write_text(OBSIDIAN_GRAPH_JSON.lstrip(), encoding="utf-8")
    (obsidian_dir / "appearance.json").write_text(OBSIDIAN_APPEARANCE_JSON.lstrip(), encoding="utf-8")
    print("  Wrote Obsidian configuration")

    project_templates = Path(__file__).resolve().parent.parent / "_templates"
    if project_templates.exists():
        for tf in project_templates.glob("*.md"):
            dest = templates_path / tf.name
            content = tf.read_text(encoding="utf-8")
            dest.write_text(content, encoding="utf-8")
        print("  Copied templates")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_only = datetime.now().strftime("%Y-%m-%d")

    _index_template = """---
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
            _index_template.format(title=title, now=now, title_lower=wd),
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

    remote = config["git"]["remote"]
    branch = config["git"]["branch"]
    if remote:
        init_repo(vault_path, remote, branch)
        print("  Initialized git repository")

    try:
        result = subprocess.run(
            ["notesmd-cli", "add-vault", str(vault_path), "--set-default"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"  Warning: Could not register vault with notesmd-cli: {result.stderr.strip()}")
        else:
            print("  Registered vault with notesmd-cli")
    except FileNotFoundError:
        print("  Warning: notesmd-cli not found. Install it to enable CLI operations.")
        print("    Windows: scoop install notesmd-cli")
        print("    macOS/Linux: brew install yakitrak/yakitrak/notesmd-cli")

    print(f"\nVault initialized: {vault_path}")
    print("Next steps:")
    print("  - Open the vault in Obsidian")
    print("  - Start creating notes with: python scripts/obsidian_mgr.py create <name> --type concept")
