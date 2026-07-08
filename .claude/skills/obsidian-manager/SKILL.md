---
name: obsidian-manager
description: >
  Manage an Obsidian vault via notesmd-cli. Create, edit, search, move, and delete notes
  with automatic frontmatter injection. Handle file attachments with wikilink references.
  Enforce Obsidian conventions (wikilinks, folder structure, frontmatter standards).
  Auto-sync vault to remote git every 30 minutes (pull + push, conflicts keep local).
  Run lint health checks (orphans, dead links, stale content, missing frontmatter).
  Maintain a structured knowledge base with typed pages (concept, entity, source,
  comparison, question) and templates.
---

# Obsidian Manager Skill

## First-Time Setup

When the user asks to initialize a vault, set up Obsidian manager, or run setup for the first time, read `docs/01-init.md` and follow the interactive flow. It will guide you through:
1. Checking prerequisites (git, notesmd-cli)
2. Asking the user for vault path, name, and git remote
3. Configuring `obsidian-manager.json`
4. Running `python scripts/obsidian_mgr.py init`
5. Verifying the result

Do NOT load `docs/01-init.md` for routine operations (create, search, sync, lint). Reserve it for first-time setup and re-initialization requests.

## Creating Notes — Categorization Workflow

**Always classify new notes into a domain.** Before creating a note:

1. **List existing domains** in the vault:
   ```
   python scripts/obsidian_mgr.py list wiki/domains
   ```

2. **Analyze the note's content** to determine which domain it belongs to. A note about "茅台股价分析" belongs to "股票知识", not "经济学原理". Choose the most specific matching domain.

3. **If a matching domain exists**, create the note with `--domain`:
   ```
   python scripts/obsidian_mgr.py create "茅台股价分析" --type concept --domain "股票知识"
   ```

4. **If no matching domain exists**, first ask the user if they want to create a new domain, then create both:
   ```
   python scripts/obsidian_mgr.py create "股票知识" --type concept --domain "股票知识"
   python scripts/obsidian_mgr.py create "茅台分析" --type concept --domain "股票知识" --related "[[A股市场]]"
   ```
   (The first `create` with `--domain "股票知识"` will auto-create the domain page.)

5. **Use `--related`** to link to other related notes when appropriate.

**Rule: Every typed note MUST have a `--domain`. Never create a note without specifying its domain.**

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
| `create` | `python scripts/obsidian_mgr.py create <name> [--type ...] --domain "..." [--related "[[...]]" ...] [--content "..."] [--open]` |
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
