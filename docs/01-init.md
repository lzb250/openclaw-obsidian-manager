# Initialization

> **For openclaw**: Read this document top to bottom. Ask the user one question at a time. Use their answers to run each command. Do not skip steps.

## 0. Pre-check

Before starting, verify prerequisites exist on the system. Run each check silently and report results:

```
git --version
notesmd-cli --version
```

If `notesmd-cli` is missing, tell the user to install it:
- **Windows**: `scoop install notesmd-cli` (requires [Scoop](https://scoop.sh/))
- **macOS/Linux**: `brew install yakitrak/yakitrak/notesmd-cli`

If `git` is missing, tell the user to install it from https://git-scm.com.

Stop here until both are available. Do not proceed with missing prerequisites.

---

## 1. Collect Vault Path

Ask the user:

> "Where is your Obsidian vault (or where do you want to create it)? Provide the absolute path."

Examples to show the user:
- Windows: `D:/obsidianDate/my-vault`
- macOS: `/Users/name/Documents/my-vault`
- Linux: `/home/name/Documents/my-vault`

The directory **does not need to exist yet** — `init` will create it if needed.

Once the user provides a path, configure it:

```
python scripts/obsidian_mgr.py config --set vault.path "<path>"
```

---

## 2. Collect Vault Name

Ask the user:

> "What name do you want for this vault? (default: the directory name)"

If they provide a name, configure it:

```
python scripts/obsidian_mgr.py config --set vault.name "<name>"
```

Otherwise, derive it from the directory name: the last segment of `vault.path`.

---

## 3. Collect Git Remote

Ask the user:

> "Do you want to sync this vault to a remote git repository? If so, provide the URL (e.g. https://github.com/user/my-vault.git). Reply 'skip' to set up later."

If they provide a URL:

```
python scripts/obsidian_mgr.py config --set git.remote "<url>"
```

If they skip, the vault will be initialized with a local git repo only. They can add a remote later with `config --set git.remote <url>`.

---

## 4. Review Configuration

Show the user what you've collected:

```
python scripts/obsidian_mgr.py config --show
```

Ask:

> "Here's the configuration. Does this look correct? (yes/no)"

If no, go back to the relevant step. If yes, proceed.

---

## 5. Initialize the Vault

Run:

```
python scripts/obsidian_mgr.py init
```

This performs:
1. Creates the vault directory (if it doesn't exist)
2. Scaffolds `wiki/` with 7 subdirectories (concepts, entities, sources, questions, comparisons, domains, meta)
3. Creates `.raw/` for immutable source documents
4. Writes `.obsidian/app.json`, `.obsidian/graph.json`, `.obsidian/appearance.json`
5. Copies `_templates/` from the project to the vault
6. Creates seed pages: `wiki/index.md`, `wiki/hot.md`, `wiki/log.md`, `wiki/overview.md`
7. Initializes git repo + first commit (if remote is configured)
8. Registers the vault with `notesmd-cli`

---

## 6. Verify

Run a quick check:

```
python scripts/obsidian_mgr.py lint
```

If there are any issues (there shouldn't be on a fresh init), report them to the user.

Then confirm:

> "Vault initialized successfully. You can now:
> - Open it in Obsidian
> - Create notes: `python scripts/obsidian_mgr.py create "Note Name" --type concept`
> - Search: `python scripts/obsidian_mgr.py search --content "query"`
> - The vault will auto-sync to remote every 30 minutes"

---

## Re-initialization

Running `init` on an already-initialized vault is **idempotent**. It will:
- Create any missing directories
- Overwrite Obsidian config files with latest defaults
- Copy any new templates from the project
- **Not** overwrite existing wiki pages (index, hot, log, overview)

If the user wants to re-initialize, just run `init` again. No need to repeat the question flow unless the vault path has changed.
