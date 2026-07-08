# Obsidian Conventions

## Wikilinks

All internal note references use `[[note-name]]` format. When creating or moving notes, wikilinks are automatically updated by `notesmd-cli`.

## Frontmatter

Every note must have YAML frontmatter with these fields:

```yaml
---
title: Note Title
tags: [tag1, tag2]
created: 2026-07-08 12:00:00
modified: 2026-07-08 12:00:00
---
```

The `create` and `edit` commands auto-inject frontmatter if missing. The `fm` command lets you read/edit/delete individual fields.

Date format is configurable in `obsidian-manager.json` under `conventions.frontmatter.date_format`.

## Directory Structure

| Directory | Purpose | Config Key |
|-----------|---------|------------|
| `attachments/` | Images, PDFs, and other files | `conventions.attachment_dir` |
| `daily/` | Daily notes | `conventions.daily_dir` |
| `templates/` | Note templates | `conventions.template_dir` |

## Attachments

Use `attach` to copy files into the vault. The command copies the file to the configured attachment directory and returns a wikilink reference:

```
> python scripts/obsidian_mgr.py attach "C:/Users/me/photo.png"
[[attachments/photo.png]]
```
