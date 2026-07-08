# Obsidian Manager Skill Design

Date: 2026-07-08
Status: Draft
Author: openclaw-obsidian-manager

## 1. Overview

An openclaw skill that manages an Obsidian vault via `notesmd-cli` (formerly `obsidian-cli`), enforces Obsidian conventions, and periodically syncs to a remote git repository.

### 1.1 Core Capabilities

- Create, edit, delete, move, search, and print notes
- Manage YAML frontmatter
- Handle attachments (copy into vault, return `[[wikilink]]`)
- Enforce Obsidian conventions: wikilinks, frontmatter fields, folder structure
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
├── docs/
│   ├── 01-init.md            ← Initialization: install notesmd-cli, configure JSON, git init, first sync
│   ├── 02-conventions.md     ← Obsidian conventions: frontmatter, wikilinks, directory structure
│   ├── 03-commands.md        ← Detailed command usage, parameters, examples
│   ├── 04-sync.md            ← Sync mechanism: flow, conflict resolution, failure recovery
│   └── 05-troubleshooting.md ← FAQ and troubleshooting
├── scripts/
│   ├── obsidian_mgr.py       ← Main CLI entry point
│   ├── vault.py              ← Note CRUD, frontmatter, search, daily notes
│   ├── sync.py               ← Git sync logic
│   ├── conventions.py        ← Obsidian conventions enforcement (wikilinks, frontmatter templates)
│   └── config.py             ← JSON config read/write
```

### 2.1 Progressive Disclosure

SKILL.md is minimal -- only overview, scheduled task declaration, command cheat sheet, and index to `docs/`. Detailed instructions live in `docs/` and are loaded by openclaw on demand. Scripts are modularized by responsibility under `scripts/`.

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
      "required_fields": ["title", "tags", "created", "modified"],
      "date_format": "YYYY-MM-DD HH:mm:ss"
    },
    "wikilinks": true
  }
}
```

- `config --show` prints entire config
- `config --set vault.path "new/path"` updates any field
- All scripts read config at startup

## 4. CLI Commands

```
obsidian_mgr.py create  <name>  [--content "..."] [--open]
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
obsidian_mgr.py config           [--show | --set key val]
```

### 4.1 Auto-Enforcement

- `create` / `edit` injects standard frontmatter (`title`, `tags`, `created`, `modified`) if missing
- `attach` copies file to `conventions.attachment_dir`, returns `[[wikilink]]` reference
- `move` delegates to `notesmd-cli move` to auto-update wikilinks across vault
- `daily` respects vault's `.obsidian/daily-notes.json` settings

## 5. Git Sync

### 5.1 Trigger

openclaw scheduled task declared in SKILL.md:

```markdown
## Scheduled Tasks
- `obsidian_sync`: every 30 minutes execute `python scripts/obsidian_mgr.py sync`
```

### 5.2 Sync Flow

1. Verify vault path exists and is a git repository
2. `git pull --rebase -X theirs origin <branch>` -- conflicts resolved with local
3. `git add -A`
4. `git diff --cached --quiet` to check for changes
5. If changes: `git commit -m "auto: sync YYYY-MM-DD HH:mm:ss"` then `git push origin <branch>`
6. If no changes: skip commit/push

### 5.3 Edge Cases

- No network: skip push, log warning
- No changes since last sync: skip commit/push
- Branch doesn't exist: auto-detect current branch and push to it
- First run (no git repo): auto `git init` + `git remote add` + first commit

## 6. Obsidian Conventions

- **Wikilinks**: All internal note references use `[[note-name]]` format
- **Frontmatter**: Every note must have `title`, `tags`, `created`, `modified` in YAML
- **Attachments**: Stored under `conventions.attachment_dir`, referenced via `[[dir/filename.ext]]`
- **Daily notes**: Stored under `conventions.daily_dir`, named per vault's daily-notes.json config
- **Templates**: Sourced from `conventions.template_dir`

## 7. Error Handling

- Config file missing: prompt to run `init` flow (load `docs/01-init.md`)
- `notesmd-cli` not installed: prompt to install via scoop/homebrew
- Vault path invalid: error with path, suggest `config --set vault.path`
- Git operations fail: log error, continue with note operations unaffected
- Sync fails: log to stderr, do not block note operations

## 8. Dependencies

- Python >= 3.8
- `notesmd-cli` (installed via scoop on Windows, homebrew on macOS/Linux)
- `git` (system)
- No Python pip packages required (stdlib only: `subprocess`, `json`, `pathlib`, `argparse`, `datetime`)
