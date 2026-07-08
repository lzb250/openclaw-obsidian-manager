# Command Reference

## create -- Create a new note

```
python scripts/obsidian_mgr.py create <name> [--content "..."] [--open]
```

- `name`: Note name (with or without `.md` extension, can include subdirectory path)
- `--content`: Initial note content (optional)
- `--open`: Open in Obsidian after creation (optional)

Auto-injects frontmatter with `title`, `tags`, `created`, `modified`.

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
