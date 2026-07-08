# Obsidian Manager Skill

Manage an Obsidian vault -- create, edit, search, and organize notes using `notesmd-cli`, with automated git sync, knowledge base structure, and health checks.

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
| `create` | `python scripts/obsidian_mgr.py create <name> [--content "..."] [--type concept\|entity\|source\|comparison\|question] [--open]` |
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
