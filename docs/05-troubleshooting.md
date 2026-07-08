# Troubleshooting

## Config file not found

```
Config file not found: .../obsidian-manager.json
Run 'python scripts/obsidian_mgr.py init' to set up.
```

Create the config file by copying the default template:
```
# On first run, create from template
python -c "from scripts.config import save_config; import json; save_config(json.load(open('obsidian-manager.json','r',encoding='utf-8')))"
```
Then edit with your vault path and git remote.

## notesmd-cli: command not found

Install notesmd-cli for your platform:
- Windows: `scoop install notesmd-cli`
- macOS/Linux: `brew install yakitrak/yakitrak/notesmd-cli`

Verify: `notesmd-cli --help`

## Vault not registered

If notesmd-cli commands fail with vault-not-found errors:
```
notesmd-cli add-vault "/path/to/vault" --set-default
notesmd-cli list-vaults  # verify it's registered
```

## Git push fails

- Check remote URL: `python scripts/obsidian_mgr.py config --show | grep remote`
- Verify git credentials are configured
- Check network connectivity
- Sync failures do not block note operations

## Python import errors

Run from the project root directory:
```
python scripts/obsidian_mgr.py --help
```

The imports use absolute paths resolved from the project root.
