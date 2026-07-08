# Git Sync Mechanism

## Trigger

Sync runs as an openclaw scheduled task every 30 minutes (configurable via `git.auto_sync_minutes`).

## Flow

1. Verify vault path exists
2. Initialize git repo if not already (first run only)
3. `git pull --rebase -X theirs origin <branch>` -- pull remote changes, resolve conflicts with local
4. `git add -A` -- stage all changes
5. Check for staged changes with `git diff --cached --quiet`
6. If changes: `git commit -m "auto: sync <timestamp>"` then `git push origin <branch>`
7. If no changes: skip

## Conflict Resolution

Conflicts are resolved with `-X theirs` during pull, meaning **local changes win**. If both sides modify the same file, the rebase keeps the local version.

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| No network | Push fails, logged to stderr, returns non-zero |
| No changes to sync | Commit/push skipped, returns success |
| Branch doesn't exist on remote | Push creates the branch |
| First run (no .git) | Auto-init + first commit |
| Vault path gone | Error, returns non-zero |

## Manual Sync

```
python scripts/obsidian_mgr.py sync
```

Run anytime to force an immediate sync.
