# Obsidian Conventions

## Wikilinks

All internal note references use `[[note-name]]` format. When creating or moving notes, wikilinks are automatically updated by `notesmd-cli`.

## Frontmatter

Every wiki note must have YAML frontmatter. Two levels of schema:

**Universal fields (all pages):**

```yaml
---
type: <concept|entity|source|comparison|question>
title: "Page Title"
created: 2026-07-08
updated: 2026-07-08
tags: [tag1, tag2]
status: seed | developing | mature | evergreen
related: ["[[Page A]]"]
sources: ["[[.raw/source.md]]"]
---
```

**Type-specific fields** are injected automatically when using `create --type`. See `docs/06-knowledge-structure.md` for full schema details.

The `create` and `edit` commands auto-inject frontmatter. The `fm` command lets you read/edit/delete individual fields.

Date format is configurable in `obsidian-manager.json` under `conventions.frontmatter.date_format`.

## Directory Structure

| Directory | Purpose | Config Key |
|-----------|---------|------------|
| `attachments/` | Images, PDFs, and other files | `conventions.attachment_dir` |
| `daily/` | Daily notes | `conventions.daily_dir` |
| `_templates/` | Note templates | `conventions.template_dir` |
| `wiki/` | Knowledge base | `knowledge.wiki_dir` |
| `.raw/` | Immutable source documents | `knowledge.raw_dir` |

## Attachments

Use `attach` to copy files into the vault. The command copies the file to the configured attachment directory and returns a wikilink reference:

```
> python scripts/obsidian_mgr.py attach "C:/Users/me/photo.png"
[[attachments/photo.png]]
```
