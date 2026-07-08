# Command Reference

## create -- Create a new note

```
python scripts/obsidian_mgr.py create <name> [--content "..."] [--type <type>] --domain "<domain>" [--related "[[Page A]]" ...] [--open]
```

- `name`: Note name (with or without `.md` extension)
- `--content`: Initial note content (optional)
- `--type`: Page type: `concept`, `entity`, `source`, `comparison`, or `question`. Places note in the correct wiki subdirectory and uses the corresponding template.
- `--domain` **(required for typed notes)**: Domain name. Automatically creates the domain page in `wiki/domains/` if it doesn't exist, and establishes bidirectional links between the note and its domain.
- `--related`: Related page wikilinks (repeatable). Establishes bidirectional links between the new note and each target page.
- `--open`: Open in Obsidian after creation (optional)

**Categorization workflow**: Before creating a note, list existing domains (`list wiki/domains`), analyze the content to determine the right domain, and always pass `--domain`. If no matching domain exists, ask the user whether to create one.

Without `--type`, creates a plain note at the vault root with universal frontmatter.

## edit -- Edit an existing note

```
python scripts/obsidian_mgr.py edit <name> --content "..." [--append]
```

- `name`: Note to edit
- `--content`: New content (required)
- `--append`: Append content instead of overwriting

Updates `modified` date in frontmatter.

## fm -- Manage frontmatter

```
python scripts/obsidian_mgr.py fm <name> --print
python scripts/obsidian_mgr.py fm <name> --set --key <key> --value <value>
python scripts/obsidian_mgr.py fm <name> --delete --key <key>
```

- `--print`: Display all frontmatter fields
- `--set`: Set or update a field (creates if not exists)
- `--delete`: Remove a field

## move -- Move or rename a note

```
python scripts/obsidian_mgr.py move <src> <dest> [--open]
```

Automatically updates all wikilinks across the vault.

## search -- Search notes

```
python scripts/obsidian_mgr.py search --name
python scripts/obsidian_mgr.py search --content <query>
```

- `--name`: Interactive fuzzy search by note name
- `--content`: Full-text search in note content (non-interactive)

## list -- List vault contents

```
python scripts/obsidian_mgr.py list [path]
```

## print -- Print note contents

```
python scripts/obsidian_mgr.py print <name>
```

## delete -- Delete a note

```
python scripts/obsidian_mgr.py delete <name>
```

Permanently deletes the file. Use with caution.

## daily -- Create or open daily note

```
python scripts/obsidian_mgr.py daily [--content "..."]
```

Respects vault's `.obsidian/daily-notes.json` settings (folder, date format, template).

## attach -- Attach a file to the vault

```
python scripts/obsidian_mgr.py attach <file> [--name "..."]
```

Copies file to the configured attachment directory. Returns wikilink.

## sync -- Sync vault to remote git

```
python scripts/obsidian_mgr.py sync
```

Pulls remote changes, commits local changes, pushes to remote.

## config -- Manage configuration

```
python scripts/obsidian_mgr.py config --show
python scripts/obsidian_mgr.py config --set <key> <value>
```

- `--show`: Print entire config as JSON
- `--set`: Set a config value (dot notation for nested keys, e.g. `git.auto_sync_minutes 15`)

## init -- Initialize vault structure

```
python scripts/obsidian_mgr.py init
```

One-click setup that:
1. Creates `wiki/` directory structure with all subdirectories
2. Writes Obsidian configuration (app.json, graph.json, appearance.json)
3. Copies templates from project to vault
4. Creates seed wiki pages (index.md, hot.md, log.md, overview.md)
5. Initializes git repository
6. Registers vault with notesmd-cli

## lint -- Vault health check

```
python scripts/obsidian_mgr.py lint [--fix]
```

Checks 8 categories:
- Orphan pages (no incoming wikilinks)
- Dead links ([[...]] pointing to non-existent pages)
- Stale content (last updated > 90 days ago)
- Missing frontmatter
- Type mismatch (type field vs parent directory)
- Empty pages (frontmatter only, no body)
- Stale index entries (index.md references deleted pages)
- Ambiguous names (same name in multiple directories)

`--fix` flag auto-corrects correctable issues.
