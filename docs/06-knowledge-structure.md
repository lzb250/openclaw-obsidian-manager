# Knowledge Base Structure

## Directory Layout

```
wiki/
├── index.md            # Master catalog: all pages by type with one-line summaries
├── hot.md              # Hot cache: ~500-word recent context summary
├── log.md              # Append-only operation log (newest at top)
├── overview.md         # Vault summary
├── concepts/           # Ideas, patterns, frameworks (+ _index.md)
├── entities/           # People, orgs, products, repositories (+ _index.md)
├── sources/            # Source document summaries (+ _index.md)
├── questions/          # Filed answers (+ _index.md)
├── comparisons/        # Side-by-side analyses (+ _index.md)
├── domains/            # Top-level topic areas (+ _index.md)
└── meta/               # Dashboards, lint reports (+ _index.md)
```

## Page Types

### concept -- Ideas, patterns, frameworks

```yaml
type: concept
complexity: basic | intermediate | advanced
domain: ""
aliases: []
```

### entity -- People, organizations, products

```yaml
type: entity
entity_type: person | organization | product | repository
role: ""
first_mentioned: ""
```

### source -- Source document summaries

```yaml
type: source
source_type: article | book | video | podcast | paper
author: ""
date_published: ""
url: ""
confidence: high | medium | low
key_claims: []
```

### comparison -- Side-by-side analyses

```yaml
type: comparison
subjects: []
dimensions: []
verdict: ""
```

### question -- Filed answers

```yaml
type: question
question: ""
answer_quality: draft | solid | definitive
```

## Status Lifecycle

```
seed -> developing -> mature -> evergreen
```

- **seed**: New page, minimal content
- **developing**: Actively being expanded
- **mature**: Comprehensive, stable
- **evergreen**: Requires minimal updates

## Workflows

### Create with type

```
python scripts/obsidian_mgr.py create "Machine Learning" --type concept
```

Creates the note in `wiki/concepts/`, uses `_templates/concept.md`, injects per-type frontmatter.

### Lint

```
python scripts/obsidian_mgr.py lint
```

Checks 8 categories: orphans, dead links, stale content, missing frontmatter, type mismatches, empty pages, stale index entries, ambiguous names.
