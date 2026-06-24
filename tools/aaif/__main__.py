"""
aaif CLI — python -m aaif <command> <file>

Commands:
  validate   Validate an AAIF document. Exits 0 if valid, 1 if invalid.
  info       Print a summary of an AAIF agent definition.
  convert    Convert an AAIF agent definition to a target framework config.

Examples:
  python -m aaif validate  examples/invoice-chaser.json
  python -m aaif info      examples/research-summarizer.json
  python -m aaif convert   examples/orchestrator-pipeline.json --target langgraph
  python -m aaif convert   examples/invoice-chaser.json --target crewai
"""
from __future__ import annotations

import argparse
import json
import sys

from . import load, validate, info as agent_info


def cmd_validate(args: argparse.Namespace) -> int:
    import os
    with open(args.file, encoding="utf-8") as f:
        data = json.load(f)
    errors = validate(data)
    if errors:
        print(f"INVALID  {args.file}")
        for e in errors:
            print(f"  {e}")
        return 1
    else:
        print(f"VALID  {args.file}")
        return 0


def cmd_info(args: argparse.Namespace) -> int:
    with open(args.file, encoding="utf-8") as f:
        data = json.load(f)
    errors = validate(data)
    if errors:
        print(f"INVALID  {args.file}")
        for e in errors:
            print(f"  {e}")
        return 1

    summary = agent_info(data)
    col_w = max(len(k) for k in summary) + 2
    for k, v in summary.items():
        print(f"  {k:<{col_w}} {v}")
    return 0


def cmd_convert(args: argparse.Namespace) -> int:
    with open(args.file, encoding="utf-8") as f:
        data = json.load(f)
    errors = validate(data)
    if errors:
        print(f"INVALID  {args.file}")
        for e in errors:
            print(f"  {e}")
        return 1

    from . import converters
    targets = {
        "langgraph":        converters.to_langgraph,
        "crewai":           converters.to_crewai,
        "autogen":          converters.to_autogen,
        "openai_assistant": converters.to_openai_assistant,
    }
    target = args.target.lower()
    if target not in targets:
        print(f"Unknown target '{args.target}'. Supported: {list(targets.keys())}")
        return 1

    result = targets[target](data)

    print(f"── {target.upper()} config ──")
    print(json.dumps(result["config"], indent=2))

    if result["unmapped"]:
        print(f"\n── Unmapped AAIF fields ──")
        print(json.dumps(result["unmapped"], indent=2))

    if result["warnings"]:
        print(f"\n── Warnings ──")
        for w in result["warnings"]:
            print(f"  ⚠  {w}")

    return 0


def cmd_import(args: argparse.Namespace) -> int:
    """Import a foreign agent format into an AAIF document (reverse of convert)."""
    with open(args.file, encoding="utf-8") as f:
        foreign = json.load(f)

    from . import converters
    importers = {
        "openai_assistant": converters.from_openai_assistant,
    }
    source = args.source.lower()
    if source not in importers:
        print(f"Unknown source '{args.source}'. Supported: {list(importers.keys())}")
        return 1

    doc = importers[source](foreign)
    errors = validate(doc)
    print(json.dumps(doc, indent=2))
    if errors:
        print(f"\n⚠  Imported document is INCOMPLETE (validation errors):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    print(f"\n✓ Imported a valid AAIF {source} agent.", file=sys.stderr)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m aaif",
        description="AAIF (SC-006) reference implementation CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Validate an AAIF document")
    p_val.add_argument("file", help="Path to an AAIF JSON file")

    p_info = sub.add_parser("info", help="Summarise an AAIF agent definition")
    p_info.add_argument("file", help="Path to an AAIF JSON file")

    p_conv = sub.add_parser("convert", help="Convert AAIF to a target framework")
    p_conv.add_argument("file", help="Path to an AAIF JSON file")
    p_conv.add_argument(
        "--target",
        required=True,
        choices=["langgraph", "crewai", "autogen", "openai_assistant"],
        help="Target framework",
    )

    p_imp = sub.add_parser("import", help="Import a foreign agent format into AAIF")
    p_imp.add_argument("file", help="Path to a foreign agent JSON file")
    p_imp.add_argument(
        "--source",
        required=True,
        choices=["openai_assistant"],
        help="Source framework",
    )

    args = parser.parse_args()
    if args.command == "validate":
        sys.exit(cmd_validate(args))
    elif args.command == "info":
        sys.exit(cmd_info(args))
    elif args.command == "convert":
        sys.exit(cmd_convert(args))
    elif args.command == "import":
        sys.exit(cmd_import(args))


if __name__ == "__main__":
    main()
