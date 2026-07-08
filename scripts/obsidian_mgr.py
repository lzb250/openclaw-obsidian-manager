import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.config import load_config, save_config
from scripts.init_vault import run_init
from scripts.lint import run_lint
from scripts.sync import run_sync
from scripts.vault import (
    attach_file,
    create_note,
    daily_note,
    delete_note,
    edit_note,
    list_vault,
    manage_frontmatter,
    move_note,
    print_note,
    search_notes,
)


def cmd_create(args):
    config = load_config()
    create_note(config, args.name, args.content, args.open, args.type, args.domain, args.related)


def cmd_edit(args):
    config = load_config()
    edit_note(config, args.name, args.content, args.append)


def cmd_fm(args):
    config = load_config()
    if args.print:
        manage_frontmatter(config, args.name, "print")
    elif args.set:
        manage_frontmatter(config, args.name, "set", args.key, args.value)
    elif args.delete:
        manage_frontmatter(config, args.name, "delete", key=args.key)


def cmd_move(args):
    config = load_config()
    move_note(config, args.src, args.dest, args.open)


def cmd_search(args):
    config = load_config()
    by = "name" if args.name else "content"
    query = args.query
    search_notes(config, by, query)


def cmd_list(args):
    config = load_config()
    list_vault(config, args.path)


def cmd_print(args):
    config = load_config()
    print_note(config, args.name)


def cmd_delete(args):
    config = load_config()
    delete_note(config, args.name)


def cmd_daily(args):
    config = load_config()
    daily_note(config, args.content)


def cmd_attach(args):
    config = load_config()
    attach_file(config, args.file, args.name)


def cmd_sync(args):
    config = load_config()
    success = run_sync(config)
    sys.exit(0 if success else 1)


def cmd_init(args):
    config = load_config()
    run_init(config)


def cmd_lint(args):
    config = load_config()
    run_lint(config, args.fix)


def cmd_config(args):
    config = load_config()
    if args.show:
        import json
        print(json.dumps(config, indent=2, ensure_ascii=False))
    elif args.set:
        if args.key is None or args.value is None:
            print("Usage: config --set <key> <value>", file=sys.stderr)
            return
        key_parts = args.key.split(".")
        value = args.value
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
        target = config
        for part in key_parts[:-1]:
            target = target[part]
        target[key_parts[-1]] = value
        save_config(config)
        print(f"Set {args.key} = {value}")


def main():
    parser = argparse.ArgumentParser(description="Obsidian Vault Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_create = subparsers.add_parser("create", help="Create a new note")
    p_create.add_argument("name", help="Note name or path")
    p_create.add_argument("--content", help="Note content")
    p_create.add_argument("--open", action="store_true", help="Open in Obsidian after creation")
    p_create.add_argument("--type", choices=["concept","entity","source","comparison","question"],
                          help="Note type (uses template and wiki subdirectory)")
    p_create.add_argument("--domain", help="Domain name (creates domain page if missing, adds backlink)")
    p_create.add_argument("--related", nargs="*", default=None,
                          help="Related page wikilinks, e.g. --related '[[Page A]]' '[[Page B]]'")
    p_create.set_defaults(func=cmd_create)

    p_edit = subparsers.add_parser("edit", help="Edit an existing note")
    p_edit.add_argument("name", help="Note name or path")
    p_edit.add_argument("--content", required=True, help="Content to write")
    p_edit.add_argument("--append", action="store_true", help="Append instead of overwrite")
    p_edit.set_defaults(func=cmd_edit)

    p_fm = subparsers.add_parser("fm", help="Manage frontmatter")
    p_fm.add_argument("name", help="Note name or path")
    fm_group = p_fm.add_mutually_exclusive_group(required=True)
    fm_group.add_argument("--print", action="store_true", help="Print frontmatter")
    fm_group.add_argument("--set", action="store_true", help="Set a frontmatter field")
    fm_group.add_argument("--delete", action="store_true", help="Delete a frontmatter field")
    p_fm.add_argument("--key", help="Frontmatter key")
    p_fm.add_argument("--value", help="Frontmatter value")
    p_fm.set_defaults(func=cmd_fm)

    p_move = subparsers.add_parser("move", help="Move or rename a note")
    p_move.add_argument("src", help="Source note path")
    p_move.add_argument("dest", help="Destination note path")
    p_move.add_argument("--open", action="store_true", help="Open after move")
    p_move.set_defaults(func=cmd_move)

    p_search = subparsers.add_parser("search", help="Search notes")
    search_group = p_search.add_mutually_exclusive_group()
    search_group.add_argument("--name", action="store_true", help="Search by note name (fuzzy)")
    search_group.add_argument("--content", action="store_true", help="Search by note content")
    p_search.add_argument("query", nargs="?", default="", help="Search query")
    p_search.set_defaults(func=cmd_search)

    p_list = subparsers.add_parser("list", help="List vault contents")
    p_list.add_argument("path", nargs="?", default=None, help="Subdirectory path")
    p_list.set_defaults(func=cmd_list)

    p_print = subparsers.add_parser("print", help="Print note contents")
    p_print.add_argument("name", help="Note name or path")
    p_print.set_defaults(func=cmd_print)

    p_delete = subparsers.add_parser("delete", help="Delete a note")
    p_delete.add_argument("name", help="Note name or path")
    p_delete.set_defaults(func=cmd_delete)

    p_daily = subparsers.add_parser("daily", help="Create/open daily note")
    p_daily.add_argument("--content", help="Content to add")
    p_daily.set_defaults(func=cmd_daily)

    p_attach = subparsers.add_parser("attach", help="Attach a file to the vault")
    p_attach.add_argument("file", help="Path to the file")
    p_attach.add_argument("--name", help="Custom filename in vault")
    p_attach.set_defaults(func=cmd_attach)

    p_sync = subparsers.add_parser("sync", help="Sync vault to remote git")
    p_sync.set_defaults(func=cmd_sync)

    p_init = subparsers.add_parser("init", help="Initialize vault structure")
    p_init.set_defaults(func=cmd_init)

    p_lint = subparsers.add_parser("lint", help="Run vault health check")
    p_lint.add_argument("--fix", action="store_true", help="Auto-fix issues")
    p_lint.set_defaults(func=cmd_lint)

    p_config = subparsers.add_parser("config", help="Manage configuration")
    p_config.add_argument("--show", action="store_true", help="Display current config")
    p_config.add_argument("--set", action="store_true", help="Set a config value")
    p_config.add_argument("key", nargs="?", default=None, help="Config key (dot notation, e.g. vault.path)")
    p_config.add_argument("value", nargs="?", default=None, help="Config value")
    p_config.set_defaults(func=cmd_config)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
