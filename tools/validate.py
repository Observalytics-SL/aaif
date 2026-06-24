#!/usr/bin/env python3
"""Validate AAIF examples against the JSON Schema definitions."""

import json
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("Install jsonschema first:  pip install jsonschema")

REPO_ROOT = Path(__file__).parent.parent
SCHEMA_DIR = REPO_ROOT / "schema"
EXAMPLES_DIR = REPO_ROOT / "examples"

STRIP_KEYS = {"x-sc-schema", "_comment", "_proposal_status"}


def load_schemas():
    schemas = {}
    for path in sorted(SCHEMA_DIR.glob("*.json")):
        with path.open() as f:
            s = json.load(f)
        schemas[path.name] = (s, path)
    return schemas


def pick_schema(example: dict, schemas: dict):
    key = example.get("x-sc-schema")
    if key:
        name = Path(key).name
        if name in schemas:
            return schemas[name]
    # Fall back to first schema alphabetically
    return next(iter(schemas.values()))


def validate_example(path: Path, schemas: dict):
    with path.open() as f:
        raw = json.load(f)
    schema_tuple = pick_schema(raw, schemas)
    schema_def, schema_path = schema_tuple
    instance = {k: v for k, v in raw.items() if k not in STRIP_KEYS}
    try:
        Draft202012Validator(schema_def).validate(instance)
        print(f"  PASS  {path.name}  ({schema_path.name})")
        return True
    except jsonschema.ValidationError as e:
        print(f"  FAIL  {path.name}: {e.message}")
        return False


def main():
    schemas = load_schemas()
    if not schemas:
        sys.exit(f"No schemas found in {SCHEMA_DIR}")

    examples = sorted(EXAMPLES_DIR.glob("*.json"))
    if not examples:
        sys.exit(f"No examples found in {EXAMPLES_DIR}")

    passed = failed = 0
    for ex in examples:
        if validate_example(ex, schemas):
            passed += 1
        else:
            failed += 1

    print(f"\n{passed} valid, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
