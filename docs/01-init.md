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

3. **Obsidian vault**: An existing vault directory on your filesystem.

## Setup

1. Edit `obsidian-manager.json` and set:
   - `vault.path` -- absolute path to your Obsidian vault
   - `vault.name` -- vault name (use directory name)
   - `git.remote` -- remote repository URL (e.g. `https://github.com/user/vault.git`)

   Or use the CLI:
   ```
   python scripts/obsidian_mgr.py config --set vault.path "D:/obsidianDate/my-vault"
   python scripts/obsidian_mgr.py config --set vault.name "my-vault"
   python scripts/obsidian_mgr.py config --set git.remote "https://github.com/user/my-vault.git"
   ```

2. Register the vault with notesmd-cli:
   ```
   notesmd-cli add-vault "D:/obsidianDate/my-vault" --set-default
   ```

3. Initialize git in the vault (auto-done on first sync, or manually):
   ```
   python scripts/obsidian_mgr.py sync
   ```

4. Verify setup:
   ```
   python scripts/obsidian_mgr.py config --show
   python scripts/obsidian_mgr.py list
   ```
