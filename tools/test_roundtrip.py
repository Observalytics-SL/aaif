#!/usr/bin/env python3
"""
Schema Commons — AAIF (SC-006) interoperability round-trip test.

Proves that portability is real, not aspirational: for the Core+Tooled field
set, converting an AAIF agent to an OpenAI Assistants object and back yields an
equivalent AAIF document.

    AAIF  --to_openai_assistant-->  Assistant  --from_openai_assistant-->  AAIF'

We assert AAIF' validates and that the agreed "lossless field set" is preserved
exactly. Fields with no Assistants equivalent are carried in metadata['x-aaif'],
so they survive too.

Usage:
    python tools/test_roundtrip.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"

from aaif import validate  # noqa: E402
from aaif.converters import to_openai_assistant, from_openai_assistant  # noqa: E402


def _get(d: dict, path: str):
    """Resolve a dotted path with [i] indices, e.g. agent.tools[0].name."""
    cur = d
    for part in path.replace("]", "").split("."):
        if "[" in part:
            key, idx = part.split("[")
            cur = cur.get(key, [])[int(idx)]
        else:
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


# AAIF documents to round-trip, with the field paths that MUST survive intact.
CASES: list[tuple[str, dict, list[str]]] = [
    (
        "tooled-function-agent",
        {
            "sc_standard": "SC-006",
            "sc_version": "3.4.0",
            "agent_id": "f0000001-0000-4000-8000-00000000aaif",
            "agent": {
                "name": "Weather Assistant",
                "goal": "Answer weather questions using the lookup tool.",
                "instructions": "You are concise and always cite the source city.",
                "model": {
                    "provider": "openai",
                    "preferred": "gpt-4o",
                    "temperature": 0.2,
                    "params": {"top_p": 0.9},
                    "response_format": "json",
                },
                "tools": [
                    {
                        "name": "get_weather",
                        "description": "Look up current weather for a city.",
                        "protocol": "function",
                        "parameters_schema": {
                            "type": "object",
                            "required": ["city"],
                            "properties": {"city": {"type": "string"}},
                        },
                    }
                ],
            },
        },
        [
            "agent.name", "agent.goal", "agent.instructions",
            "agent.model.provider", "agent.model.preferred",
            "agent.model.temperature", "agent.model.params.top_p",
            "agent.model.response_format",
            "agent.tools[0].name", "agent.tools[0].description",
            "agent.tools[0].protocol", "agent.tools[0].parameters_schema",
            "agent_id", "sc_version",
        ],
    ),
    (
        "custom-provider-agent",
        {
            "sc_standard": "SC-006",
            "agent": {
                "name": "Gateway Agent",
                "goal": "Route through a self-hosted gateway.",
                "model": {"provider": "custom", "provider_id": "litellm", "preferred": "gpt-4o"},
            },
        },
        ["agent.name", "agent.goal", "agent.model.provider", "agent.model.provider_id", "agent.model.preferred"],
    ),
]


def main() -> int:
    print(f"\n{DIM}── AAIF round-trip interop suite  (OpenAI Assistants){RESET}")
    failures = 0
    checks = 0

    for name, original, lossless in CASES:
        # forward + back
        assistant = to_openai_assistant(original)["config"]
        restored = from_openai_assistant(assistant)

        # restored must be valid AAIF
        checks += 1
        errs = validate(restored)
        if errs:
            failures += 1
            print(f"  {RED}✗ {name}: restored doc invalid{RESET}")
            for e in errs[:4]:
                print(f"      {e}")
            continue

        # every lossless path must match
        mismatched = []
        for path in lossless:
            checks += 1
            if _get(original, path) != _get(restored, path):
                failures += 1
                mismatched.append(path)
        if mismatched:
            print(f"  {RED}✗ {name}: fields changed across round-trip: {mismatched}{RESET}")
            for p in mismatched:
                print(f"      {p}: {_get(original, p)!r} -> {_get(restored, p)!r}")
        else:
            print(f"  {GREEN}✓ {name}{RESET}  ({len(lossless)} fields preserved, restored doc valid)")

    print("  " + "─" * 55)
    if failures:
        print(f"  {RED}FAILED{RESET}  —  {failures} problem(s), {checks} checks run")
        return 1
    print(f"  {GREEN}ALL GOOD{RESET}  —  {checks} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
