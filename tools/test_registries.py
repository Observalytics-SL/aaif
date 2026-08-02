#!/usr/bin/env python3
"""
Schema Commons — AAIF (SC-006) registry consistency check.

Verifies that:
  1. every registries/*.json validates against registries/registry.schema.json,
  2. every value in the *recommended* schema enums is a 'standard' registry entry
     (the schema enum MUST be a subset of the registry — the registry may legitimately
     contain extra 'provisional'/'deprecated' ids the enum does not list),
  3. registry ids are unique within each file.

Usage:
    python tools/test_registries.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# Maps a registry file -> a function returning the set of enum values in the schema
# that the registry's 'standard' entries MUST cover.
def _agent_enum(schema: dict, *path: str) -> set[str]:
    node = schema
    for key in path:
        node = node[key]
    return set(node["enum"])


def main() -> int:
    base = ROOT
    reg_dir = os.path.join(base, "registries")
    agent_schema = load(os.path.join(base, "schema", "agent.schema.json"))
    manifest_schema = load(os.path.join(base, "schema", "platform-manifest.schema.json"))
    meta = load(os.path.join(reg_dir, "registry.schema.json"))

    model_props = agent_schema["properties"]["agent"]["properties"]["model"]["properties"]
    tool_props = agent_schema["properties"]["agent"]["properties"]["tools"]["items"]["properties"]
    mem_props = agent_schema["properties"]["agent"]["properties"]["memory"]["items"]["properties"]
    cond = agent_schema["$defs"]["condition"]["oneOf"][1]["properties"]["lang"]["enum"]
    vault_provider = tool_props["auth"]["properties"]["vault_ref"]["properties"]["provider"]["enum"]

    # registry file -> required subset (schema enum that standard entries must cover)
    required: dict[str, set[str]] = {
        "providers.json": set(model_props["provider"]["enum"]),
        "condition-languages.json": set(cond),
        "vault-providers.json": set(vault_provider),
        "memory-backends.json": set(mem_props["backend"]["enum"]),
        "tool-protocols.json": set(tool_props["protocol"]["enum"]),
        # capabilities: the manifest condition_languages enum must be covered by the cond-lang registry,
        # handled above; capabilities.json has no single enum mirror, so we only structurally validate it.
        "capabilities.json": set(),
    }

    try:
        from jsonschema import Draft202012Validator  # type: ignore
        meta_validator = Draft202012Validator(meta)
    except ImportError:
        meta_validator = None

    print(f"\n{DIM}── AAIF  registry suite{RESET}")
    failures = 0
    checks = 0

    for fname, must_cover in required.items():
        path = os.path.join(reg_dir, fname)
        if not os.path.exists(path):
            print(f"  {RED}✗ missing {fname}{RESET}")
            failures += 1
            continue
        reg = load(path)

        # 1. structural validation
        if meta_validator is not None:
            errs = sorted(meta_validator.iter_errors(reg), key=lambda e: list(e.path))
            checks += 1
            if errs:
                failures += 1
                print(f"  {RED}✗ {fname} fails registry.schema.json{RESET}")
                for e in errs[:5]:
                    print(f"      {list(e.path)}: {e.message}")
                continue

        ids = [e["id"] for e in reg["entries"]]
        # 3. uniqueness
        checks += 1
        if len(ids) != len(set(ids)):
            failures += 1
            dupes = {i for i in ids if ids.count(i) > 1}
            print(f"  {RED}✗ {fname} has duplicate ids: {sorted(dupes)}{RESET}")
            continue

        # 2. enum subset coverage
        standard_ids = {e["id"] for e in reg["entries"] if e["status"] == "standard"}
        checks += 1
        missing = must_cover - standard_ids
        if missing:
            failures += 1
            print(f"  {RED}✗ {fname}: schema enum values not 'standard' in registry: {sorted(missing)}{RESET}")
            continue

        print(f"  {GREEN}✓ {fname}{RESET}  ({len(ids)} ids; {len(standard_ids)} standard)")

    # cross-check: manifest condition_languages enum subset of cond-lang registry standard ids
    cl_reg = load(os.path.join(reg_dir, "condition-languages.json"))
    cl_standard = {e["id"] for e in cl_reg["entries"] if e["status"] == "standard"}
    manifest_cl = set(
        manifest_schema["properties"]["platform"]["properties"]["capabilities"]
        ["properties"]["orchestration"]["properties"]["condition_languages"]["items"]["enum"]
    )
    checks += 1
    if manifest_cl - cl_standard:
        failures += 1
        print(f"  {RED}✗ manifest condition_languages enum not covered by registry: {sorted(manifest_cl - cl_standard)}{RESET}")
    else:
        print(f"  {GREEN}✓ manifest condition_languages ⊆ registry{RESET}")

    print("  " + "─" * 55)
    if failures:
        print(f"  {RED}FAILED{RESET}  —  {failures} problem(s), {checks} checks run")
        return 1
    print(f"  {GREEN}ALL GOOD{RESET}  —  {checks} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
