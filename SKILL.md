# Obsidian Manager Skill

Manage an Obsidian vault -- create, edit, search, and organize notes using `notesmd-cli`, with automated git sync.

## Scheduled Tasks

- `obsidian_sync`: every 30 minutes execute `python scripts/obsidian_mgr.py sync`

## Quick Reference

| Command | Usage |
|---------|-------|
| `create` | `python scripts/obsidian_mgr.py create <name> [--content "..."] [--open]` |
| `edit` | `python scripts/obsidian_mgr.py edit <name> --content "..." [--append]` |
| `fm` | `python scripts/obsidian_mgr.py fm <name> --print \| --set key val \| --delete key` |
| `move` | `python scripts/obsidian_mgr.py move <src> <dest> [--open]` |
| `search` | `python scripts/obsidian_mgr.py search [--name \| --content] <query>` |
| `list` | `python scripts/obsidian_mgr.py list [path]` |
| `print` | `python scripts/obsidian_mgr.py print <name>` |
| `delete` | `python scripts/obsidian_mgr.py delete <name>` |
| `daily` | `python scripts/obsidian_mgr.py daily [--content "..."]` |
| `attach` | `python scripts/obsidian_mgr.py attach <file> [--name "..."]` |
| `sync` | `python scripts/obsidian_mgr.py sync` |
| `config` | `python scripts/obsidian_mgr.py config --show \| --set key val` |

## Documentation

- **First-time setup**: see `docs/01-init.md`
- **Obsidian conventions**: see `docs/02-conventions.md`
- **Full command reference**: see `docs/03-commands.md`
- **Sync mechanism**: see `docs/04-sync.md`
- **Troubleshooting**: see `docs/05-troubleshooting.md`
