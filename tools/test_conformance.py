#!/usr/bin/env python3
"""
AAIF Conformance Test Suite Runner
===================================
Tests that:
  - every file under tests/conformance/valid/   PASSES schema validation
  - every file under tests/conformance/invalid/ FAILS  schema validation

Usage (from repo root):
    python tools/test_conformance.py

Exit code 0 = all assertions passed.
Exit code 1 = one or more assertions failed.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X_SC_SCHEMA_KEY = "x-sc-schema"
COMMENT_KEY = "_comment"

try:
    from jsonschema import Draft202012Validator, SchemaError, ValidationError  # type: ignore
    HAVE_JSONSCHEMA = True
except ImportError:  # pragma: no cover
    HAVE_JSONSCHEMA = False


def load_schemas(schema_dir: str) -> dict[str, dict]:
    schemas: dict[str, dict] = {}
    for path in glob.glob(os.path.join(schema_dir, "*.schema.json")):
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            schemas[name] = json.load(f)
    return schemas


def validate_example(data: dict, schemas: dict[str, dict]) -> list[str]:
    """Return a list of validation error messages (empty = valid)."""
    if not HAVE_JSONSCHEMA:
        # Minimal fallback: just check required fields exist in root
        if "sc_standard" not in data:
            return ["Missing sc_standard (no jsonschema package installed)"]
        return []

    schema_name = data.get(X_SC_SCHEMA_KEY)
    if schema_name is None:
        # Fall back to first schema alphabetically
        schema_name = sorted(schemas.keys())[0]

    if schema_name not in schemas:
        return [f"Schema '{schema_name}' not found in schema/ directory"]

    schema = schemas[schema_name]
    # Strip meta/routing keys before validation
    cleaned = {k: v for k, v in data.items()
               if k not in (X_SC_SCHEMA_KEY, COMMENT_KEY)}

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(cleaned), key=lambda e: list(e.path))
    return [f"{list(e.path)}: {e.message}" for e in errors]


def run() -> int:
    schema_dir = os.path.join(ROOT, "schema")
    if not os.path.isdir(schema_dir):
        print(f"  ERROR  schema/ directory not found at {schema_dir}")
        return 1

    schemas = load_schemas(schema_dir)
    if not schemas:
        print(f"  ERROR  no *.schema.json files found in {schema_dir}")
        return 1

    tests_base = os.path.join(ROOT, "tests", "conformance")
    valid_dir   = os.path.join(tests_base, "valid")
    invalid_dir = os.path.join(tests_base, "invalid")

    passed = 0
    failed = 0

    # ── valid fixtures — must pass ──────────────────────────────────────────
    print("\n── AAIF  conformance suite")
    print("  ┌─ must-pass")
    for path in sorted(glob.glob(os.path.join(valid_dir, "*.json"))):
        name = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        errors = validate_example(data, schemas)
        if errors:
            print(f"  │  FAIL  {os.path.basename(path)}")
            for e in errors:
                print(f"  │        {e}")
            failed += 1
        else:
            print(f"  │  ✓  {os.path.basename(path)}")
            passed += 1

    # ── invalid fixtures — must fail ────────────────────────────────────────
    print("  ├─ must-reject")
    for path in sorted(glob.glob(os.path.join(invalid_dir, "*.json"))):
        name = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        errors = validate_example(data, schemas)
        if errors:
            # Correctly rejected
            print(f"  │  ✓  {os.path.basename(path)}  [{errors[0][:60]}…]")
            passed += 1
        else:
            print(f"  │  FAIL  {os.path.basename(path)}  (expected rejection but it passed!)")
            failed += 1

    # ── summary ─────────────────────────────────────────────────────────────
    total = passed + failed
    print("  └─" + "─" * 56)
    if failed == 0:
        print(f"  ALL GOOD  —  {passed}/{total} assertions passed")
    else:
        print(f"  FAILURES  —  {failed}/{total} assertions failed")
    print()

    return 0 if failed == 0 else 1


def main() -> None:
    argparse.ArgumentParser(description="AAIF Conformance Test Runner").parse_args()
    sys.exit(run())


if __name__ == "__main__":
    main()
