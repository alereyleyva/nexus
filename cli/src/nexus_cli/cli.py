from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from typing import cast

from nexus_cli.auth import LoginError, authenticate, login
from nexus_cli.client import ApiClient, ApiError
from nexus_cli.config import resolve_api_url
from nexus_cli.credentials import (
    Credentials,
    clear_credentials,
    load_credentials,
    save_credentials,
)
from nexus_cli.http import HttpError

_GROUP_LABELS: tuple[tuple[str, str], ...] = (
    ("decisions", "Decisions"),
    ("problems", "Problems"),
    ("solutions", "Solutions"),
    ("failed_attempts", "Failed attempts"),
    ("risks", "Risks"),
    ("procedures", "Procedures"),
    ("open_questions", "Open questions"),
    ("tasks", "Tasks"),
    ("notes", "Notes"),
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handler = cast("object", getattr(args, "handler", None))
    if not callable(handler):
        parser.print_help()
        return 2
    try:
        return cast(int, handler(args))
    except (ApiError, LoginError, HttpError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexus", description="Nexus shared memory CLI.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("login", help="Sign in with browser SSO.").set_defaults(handler=_login)
    subparsers.add_parser("logout", help="Revoke and forget the local session.").set_defaults(
        handler=_logout
    )
    subparsers.add_parser("whoami", help="Show the signed-in user.").set_defaults(handler=_whoami)

    memory = subparsers.add_parser("memory", help="Work with memory entries.")
    memory_sub = memory.add_subparsers(dest="memory_command")
    add = memory_sub.add_parser("add", help="Create a memory entry.")
    add.add_argument("--type", required=True)
    add.add_argument("--title", required=True)
    add.add_argument("--body", required=True, help="Body text, or '-' to read from stdin.")
    add.add_argument("--rationale")
    add.add_argument("--visibility")
    add.add_argument("--project", help="Project key, e.g. CECW.")
    add.add_argument("--group-id", help="Group UUID for group visibility.")
    add.add_argument("--tag", action="append", default=[], dest="tags")
    add.add_argument("--source-tool", default="nexus-cli")
    add.add_argument("--source-ref")
    add.set_defaults(handler=_memory_add)

    search = subparsers.add_parser("search", help="Search authorized memory.")
    search.add_argument("--query", required=True)
    search.add_argument("--project", help="Project key.")
    search.add_argument("--type", action="append", default=[], dest="types")
    search.add_argument("--tag", action="append", default=[], dest="tags")
    search.add_argument("--limit", type=int, default=10)
    search.set_defaults(handler=_search)

    pack = subparsers.add_parser("context-pack", help="Generate a task context pack.")
    pack.add_argument("--project", help="Project key.")
    pack.add_argument("--task", required=True)
    pack.add_argument("--query")
    pack.add_argument("--max-items", type=int, default=20, dest="max_items")
    pack.set_defaults(handler=_context_pack)

    return parser


def _login(args: argparse.Namespace) -> int:
    _ = args
    api_url = resolve_api_url()
    credentials = login(api_url)
    save_credentials(credentials)
    client, _refreshed = authenticate(credentials)
    identity = client.me()
    print(f"Signed in as {_text(identity, 'user_id')} in org {_text(identity, 'org_id')}.")
    return 0


def _logout(args: argparse.Namespace) -> int:
    _ = args
    credentials = load_credentials()
    if credentials is not None:
        try:
            client, _refreshed = authenticate(credentials)
            client.revoke_session()
        except (ApiError, LoginError, HttpError):
            pass  # Best effort: always clear the local session below.
    clear_credentials()
    print("Signed out.")
    return 0


def _whoami(args: argparse.Namespace) -> int:
    _ = args
    client, _refreshed = _authenticated_client()
    identity = client.me()
    capabilities = identity.get("capabilities")
    print(f"user_id: {_text(identity, 'user_id')}")
    print(f"org_id:  {_text(identity, 'org_id')}")
    print(f"client:  {_text(identity, 'client_type')}")
    if isinstance(capabilities, list) and capabilities:
        print(f"caps:    {', '.join(str(item) for item in cast(list[object], capabilities))}")
    return 0


def _memory_add(args: argparse.Namespace) -> int:
    client, _refreshed = _authenticated_client()
    body = sys.stdin.read() if args.body == "-" else args.body
    payload: dict[str, object] = {
        "type": args.type,
        "title": args.title,
        "body": body,
        "source_kind": "ai_cli",
        "source_tool": args.source_tool,
        "tags": list(args.tags),
    }
    if args.rationale:
        payload["rationale"] = args.rationale
    if args.source_ref:
        payload["source_ref"] = args.source_ref
    if args.visibility:
        payload["visibility_scope"] = args.visibility
    if args.group_id:
        payload["visibility_group_id"] = args.group_id
    if args.project:
        payload["project_id"] = _resolve_project_id(client, args.project)
    entry = client.create_memory(payload)
    status = _text(entry, "status")
    print(f"Created memory {_text(entry, 'id')} ({status}).")
    if status == "pending_review":
        print("It was proposed for review and is not active yet.")
    return 0


def _search(args: argparse.Namespace) -> int:
    client, _refreshed = _authenticated_client()
    payload: dict[str, object] = {
        "query": args.query,
        "types": list(args.types),
        "tags": list(args.tags),
        "limit": args.limit,
    }
    if args.project:
        payload["project_id"] = _resolve_project_id(client, args.project)
    response = client.search(payload)
    results = response.get("results")
    if not isinstance(results, list) or not results:
        print("No results.")
        return 0
    for item in cast(list[object], results):
        if isinstance(item, Mapping):
            row = cast(Mapping[str, object], item)
            print(f"- [{_text(row, 'type')}] {_text(row, 'title')} ({_text(row, 'status')})")
    return 0


def _context_pack(args: argparse.Namespace) -> int:
    client, _refreshed = _authenticated_client()
    payload: dict[str, object] = {"task": args.task, "max_items": args.max_items}
    if args.query:
        payload["query"] = args.query
    if args.project:
        payload["project_id"] = _resolve_project_id(client, args.project)
    pack = client.context_pack(payload)
    _render_context_pack(pack, task=args.task)
    return 0


def _render_context_pack(pack: Mapping[str, object], *, task: str) -> None:
    print(f"# Context pack: {task}\n")
    items = pack.get("items")
    if isinstance(items, Mapping):
        grouped = cast(Mapping[str, object], items)
        for key, label in _GROUP_LABELS:
            entries = grouped.get(key)
            if isinstance(entries, list) and entries:
                print(f"## {label}")
                for entry in cast(list[object], entries):
                    if isinstance(entry, Mapping):
                        print(f"- {_text(cast(Mapping[str, object], entry), 'title')}")
                print()
    warnings = pack.get("warnings")
    if isinstance(warnings, list) and warnings:
        print("## Warnings")
        for warning in cast(list[object], warnings):
            if isinstance(warning, Mapping):
                print(f"- {_text(cast(Mapping[str, object], warning), 'message')}")


def _authenticated_client() -> tuple[ApiClient, Credentials]:
    credentials = load_credentials()
    if credentials is None:
        raise LoginError("Not signed in. Run 'nexus login' first.")
    return authenticate(credentials)


def _resolve_project_id(client: ApiClient, key: str) -> str:
    projects = client.list_projects()
    items = projects.get("items")
    if isinstance(items, list):
        for item in cast(list[object], items):
            if isinstance(item, Mapping):
                row = cast(Mapping[str, object], item)
                if row.get("key") == key:
                    return _text(row, "id")
    raise LoginError(f"No visible project with key '{key}'.")


def _text(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    return value if isinstance(value, str) else ""
