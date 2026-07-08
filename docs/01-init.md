# Initialization

## Prerequisites

1. **notesmd-cli**: Install the CLI tool for your platform:
   - Windows (PowerShell):
     ```
     scoop bucket add scoop-yakitrak https://github.com/yakitrak/scoop-yakitrak.git
     scoop install notesmd-cli
     ```
   - macOS / Linux:
     ```
     brew tap yakitrak/yakitrak
     brew install yakitrak/yakitrak/notesmd-cli
     ```

2. **git**: Must be installed and available on PATH.

3. **Obsidian vault**: Create an empty directory for your vault.

## One-Click Setup

```
python scripts/obsidian_mgr.py config --set vault.path "D:/obsidianDate/my-vault"
python scripts/obsidian_mgr.py config --set vault.name "my-vault"
python scripts/obsidian_mgr.py config --set git.remote "https://github.com/user/my-vault.git"
python scripts/obsidian_mgr.py init
```

This performs:
1. Creates `wiki/` directory structure (concepts, entities, sources, etc.)
2. Writes Obsidian configuration (app.json, graph.json, appearance.json)
3. Copies templates from project to vault's `_templates/`
4. Creates seed wiki pages (index.md, hot.md, log.md, overview.md)
5. Initializes git repository
6. Registers vault with notesmd-cli

## Verify Setup

```
python scripts/obsidian_mgr.py config --show
python scripts/obsidian_mgr.py list
```
