# Obsidian Manager Skill Design

Date: 2026-07-08
Status: Draft
Author: openclaw-obsidian-manager

## 1. Overview

An openclaw skill that manages an Obsidian vault via `notesmd-cli` (formerly `obsidian-cli`), enforces Obsidian conventions, periodically syncs to a remote git repository, and maintains a structured knowledge base with init/lint workflows.

### 1.1 Core Capabilities

- Create, edit, delete, move, search, and print notes
- Manage YAML frontmatter with per-type schemas
- Handle attachments (copy into vault, return `[[wikilink]]`)
- Enforce Obsidian conventions: wikilinks, frontmatter, folder structure
- One-click vault initialization (scaffold dirs, Obsidian config, templates, git)
- Structured knowledge base: `wiki/` with typed pages, hot cache, index, log
- Template system for 6 note types (concept, entity, source, comparison, question, daily)
- Lint health check: orphans, dead links, stale content, frontmatter gaps
- Auto-sync vault to remote git (pull + push, 30-minute interval)
- Config stored as local JSON, updatable via CLI

### 1.2 Tech Stack

- **Implementation**: Python 3 scripts under `scripts/`
- **Core CLI**: `notesmd-cli` (Go binary, installed separately)
- **Git**: Native `git` commands
- **Scheduler**: openclaw built-in scheduled task declared in SKILL.md

## 2. Project Structure

```
openclaw-obsidian-manager/
├── SKILL.md                  ← Main entry: overview, scheduled task, command cheat sheet, doc index
├── obsidian-manager.json     ← Config file
├── _templates/               ← Note templates (concept, entity, source, comparison, question, daily)
├── docs/
│   ├── 01-init.md            ← Initialization guide
│   ├── 02-conventions.md     ← Obsidian conventions: frontmatter, wikilinks, directory structure
│   ├── 03-commands.md        ← Detailed command usage, parameters, examples
│   ├── 04-sync.md            ← Sync mechanism: flow, conflict resolution, failure recovery
│   ├── 05-troubleshooting.md ← FAQ and troubleshooting
│   └── 06-knowledge-structure.md ← Knowledge base design: types, schemas, workflows
├── scripts/
│   ├── obsidian_mgr.py       ← Main CLI entry point
│   ├── vault.py              ← Note CRUD, frontmatter, search, daily notes
│   ├── sync.py               ← Git sync logic
│   ├── conventions.py        ← Obsidian conventions + per-type frontmatter generation
│   ├── config.py             ← JSON config read/write
│   ├── init_vault.py         ← One-click vault initialization
│   └── lint.py               ← Vault health check
```

### 2.2 Knowledge Base Structure (created in vault by `init`)

```
{vaulth-path}/
├── wiki/
│   ├── index.md              # Master catalog: all pages by type with one-line summaries
│   ├── hot.md                # Hot cache: ~500-word recent context
│   ├── log.md                # Append-only operation log
│   ├── overview.md           # Vault summary
│   ├── concepts/             # Ideas, patterns, frameworks (+ _index.md)
│   ├── entities/             # People, orgs, products (+ _index.md)
│   ├── sources/              # Source document summaries
│   ├── questions/            # Filed answers
│   ├── comparisons/          # Side-by-side analyses
│   ├── domains/              # Top-level topic areas (+ _index.md)
│   └── meta/                 # Dashboards, lint reports
├── .raw/                     # Immutable source layer (never modified)
└── _templates/               # Note templates (copied from project on init)
```

## 3. Configuration

`obsidian-manager.json` at project root:

```json
{
  "vault": {
    "path": "D:/obsidianDate/my-vault",
    "name": "my-vault"
  },
  "git": {
    "remote": "https://github.com/user/my-vault.git",
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

- `config --show` prints entire config
- `config --set key val` updates any field (dot notation, e.g. `knowledge.stale_days 60`)
- All scripts read config at startup

## 4. CLI Commands

```
obsidian_mgr.py init                             ← One-click vault setup
obsidian_mgr.py create  <name>  [--content "..."] [--type concept|entity|source|comparison|question] [--open]
obsidian_mgr.py edit    <name>  --content "..." [--append]
obsidian_mgr.py fm      <name>  --print | --set key val | --delete key
obsidian_mgr.py move    <src>   <dest> [--open]
obsidian_mgr.py search           [--name | --content] <query>
obsidian_mgr.py list    [path]
obsidian_mgr.py print   <name>
obsidian_mgr.py delete  <name>
obsidian_mgr.py daily            [--content "..."]
obsidian_mgr.py attach  <file>   [--name "..."]
obsidian_mgr.py sync
obsidian_mgr.py lint             [--fix]
obsidian_mgr.py config           [--show | --set key val]
```

### 4.1 Auto-Enforcement

- `create --type` injects per-type frontmatter schema from template
- `create` without `--type` injects universal frontmatter
- `edit` updates `updated` date in frontmatter
- `attach` copies file to `conventions.attachment_dir`, returns `[[wikilink]]`
- `move` delegates to `notesmd-cli move` to auto-update wikilinks across vault

## 5. Knowledge Base Design

### 5.1 Page Types and Frontmatter Schemas

**Universal fields (all pages):**

```yaml
type: <concept|entity|source|comparison|question>
title: "Page Title"
created: 2026-07-08
updated: 2026-07-08
tags: [tag1, tag2]
status: seed | developing | mature | evergreen
related: ["[[Page A]]", "[[Page B]]"]
sources: ["[[.raw/source-file.md]]"]
```

**Type-specific fields:**

| Type | Extra Fields |
|------|-------------|
| `source` | `source_type`, `author`, `date_published`, `url`, `confidence` (high/medium/low), `key_claims` |
| `entity` | `entity_type` (person/organization/product/repository), `role`, `first_mentioned` |
| `concept` | `complexity` (basic/intermediate/advanced), `domain`, `aliases` |
| `comparison` | `subjects`, `dimensions`, `verdict` |
| `question` | `question` (original query), `answer_quality` (draft/solid/definitive) |

### 5.2 Templates

`_templates/` contains one `.md` file per type. `create --type concept` copies `_templates/concept.md` to the appropriate wiki subdirectory, replaces `{{title}}` and `{{date}}` placeholders.

### 5.3 Hot Cache + Index

- `wiki/index.md`: Lists every page in `wiki/` by type with one-line summary. Updated by `create`/`edit`/`delete`/`move`.
- `wiki/hot.md`: ~500 words of recent context. Updated manually or via `--update-hot` flag on relevant commands.
- `wiki/log.md`: Append-only. Every `create`/`edit`/`delete`/`move`/`sync` appends a timestamped entry.

## 6. Init Flow

`python scripts/obsidian_mgr.py init` performs:

1. **Directory scaffold** — creates `wiki/` subdirectories (concepts, entities, sources, questions, comparisons, domains, meta) and `.raw/`
2. **Obsidian config** — writes `.obsidian/app.json` (exclude system dirs), `.obsidian/graph.json` (color-coded groups by folder), `.obsidian/appearance.json`
3. **Templates** — copies `_templates/*.md` from project to vault's `_templates/`
4. **Seed pages** — creates `wiki/index.md`, `wiki/hot.md`, `wiki/log.md`, `wiki/overview.md` with initial content
5. **Git init** — initializes git repo, adds remote, first commit
6. **Register vault** — runs `notesmd-cli add-vault <path> --set-default`

Idempotent: running `init` on an existing vault only creates missing files/dirs.

## 7. Lint Health Check

`python scripts/obsidian_mgr.py lint` checks 8 categories:

| # | Check | Description |
|---|-------|-------------|
| 1 | Orphan pages | No wikilinks point to this page |
| 2 | Dead links | `[[...]]` references to non-existent pages |
| 3 | Stale content | `updated` > `knowledge.stale_days` and status in (mature, evergreen) |
| 4 | Missing frontmatter | Lacks `type`, `title`, `created`, or `updated` |
| 5 | Type mismatch | `type` field doesn't match parent directory |
| 6 | Empty pages | Only frontmatter, no body content |
| 7 | Index stale | `wiki/index.md` references deleted pages |
| 8 | Wikilink ambiguity | Two files share the same name in different directories |

`--fix` flag auto-corrects: update stale dates, add missing frontmatter, remove dead links from index. Report saved to `wiki/meta/lint-report.md`.

## 8. Git Sync (unchanged from v1)

### 8.1 Trigger

openclaw scheduled task declared in SKILL.md:

```markdown
## Scheduled Tasks
- `obsidian_sync`: every 30 minutes execute `python scripts/obsidian_mgr.py sync`
```

### 8.2 Sync Flow

1. Verify vault path exists and is a git repository
2. `git pull --rebase -X theirs origin <branch>` — conflicts resolved with local
3. `git add -A`
4. `git diff --cached --quiet` to check for changes
5. If changes: `git commit -m "auto: sync YYYY-MM-DD HH:mm:ss"` then `git push origin <branch>`
6. If no changes: skip commit/push

### 8.3 Edge Cases

- No network: skip push, log warning
- No changes since last sync: skip commit/push
- Branch doesn't exist: auto-detect current branch and push to it
- First run (no git repo): auto `git init` + `git remote add` + first commit

## 9. Error Handling

- Config file missing: prompt to run `init` flow (load `docs/01-init.md`)
- `notesmd-cli` not installed: prompt to install via scoop/homebrew
- Vault path invalid: error with path, suggest `config --set vault.path`
- Git operations fail: log error, continue with note operations unaffected
- Sync fails: log to stderr, do not block note operations

## 10. Dependencies

- Python >= 3.8
- `notesmd-cli` (installed via scoop on Windows, homebrew on macOS/Linux)
- `git` (system)
- No Python pip packages required (stdlib only: `subprocess`, `json`, `pathlib`, `argparse`, `datetime`, `shutil`)
