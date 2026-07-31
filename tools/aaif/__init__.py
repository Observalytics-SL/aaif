"""
aaif — AAIF (SC-006) Python Reference Implementation
=====================================================
Load, validate, and convert Autonomous Agent Interchange Format documents.

Quick start
-----------
    from aaif import load, validate

    agent = load("my-agent.json")          # loads + validates
    errors = validate({"sc_standard": "SC-006", ...})  # returns list of error strings

Converters (stub implementations — wire up your own runtime):
    from aaif.converters import to_langgraph, to_crewai

    graph_config  = to_langgraph(agent)
    crew_config   = to_crewai(agent)

CLI
---
    python -m aaif validate my-agent.json
    python -m aaif convert  my-agent.json --target langgraph
    python -m aaif info     my-agent.json
"""
from __future__ import annotations

import json
import os
from typing import Any

_SCHEMA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "SC-006-agent-interchange-format",
    "schema",
)

X_SC_SCHEMA_KEY = "x-sc-schema"
_COMMENT_KEY = "_comment"

# ── lazy schema cache ──────────────────────────────────────────────────────

_schemas: dict[str, dict] | None = None


def _get_schemas() -> dict[str, dict]:
    global _schemas
    if _schemas is None:
        _schemas = {}
        if os.path.isdir(_SCHEMA_DIR):
            import glob
            for path in glob.glob(os.path.join(_SCHEMA_DIR, "*.schema.json")):
                name = os.path.basename(path)
                with open(path, encoding="utf-8") as f:
                    _schemas[name] = json.load(f)
    return _schemas


# ── public API ─────────────────────────────────────────────────────────────

def validate(data: dict[str, Any]) -> list[str]:
    """
    Validate *data* against the appropriate AAIF schema.

    Returns a list of human-readable error strings.
    An empty list means the document is valid.

    The schema is selected by the 'x-sc-schema' key in *data*.
    If not present, the first schema alphabetically is used.
    """
    schemas = _get_schemas()
    if not schemas:
        raise RuntimeError(
            f"No *.schema.json files found in {_SCHEMA_DIR}. "
            "Run this from the repo root or install the aaif package properly."
        )

    schema_name = data.get(X_SC_SCHEMA_KEY)
    if schema_name is None:
        # Default to the agent definition schema (the primary document type);
        # fall back to the first available only if it is absent. Do NOT rely on
        # alphabetical order — sibling schema files (agent-state, conformance-report)
        # would otherwise shadow the agent schema.
        schema_name = (
            "agent.schema.json" if "agent.schema.json" in schemas
            else sorted(schemas.keys())[0]
        )
    if schema_name not in schemas:
        return [f"Schema '{schema_name}' not found. Available: {list(schemas.keys())}"]

    schema = schemas[schema_name]
    cleaned = {k: v for k, v in data.items() if k not in (X_SC_SCHEMA_KEY, _COMMENT_KEY)}

    try:
        from jsonschema import Draft202012Validator  # type: ignore
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(cleaned), key=lambda e: list(e.path))
        return [f"{list(e.path)}: {e.message}" for e in errors]
    except ImportError:
        # Minimal fallback without jsonschema package
        missing = []
        if "sc_standard" not in cleaned:
            missing.append("Missing required field: sc_standard")
        if "agent" in cleaned:
            agent = cleaned["agent"]
            if not isinstance(agent, dict):
                missing.append("'agent' must be an object")
            else:
                for req in ("name", "goal"):
                    if req not in agent:
                        missing.append(f"Missing required field: agent.{req}")
        return missing


def load(path: str) -> dict[str, Any]:
    """
    Load an AAIF document from *path*, validate it, and return the parsed dict.

    Raises ValueError if validation fails.
    Raises FileNotFoundError if the file does not exist.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    errors = validate(data)
    if errors:
        lines = "\n  ".join(errors)
        raise ValueError(f"AAIF validation failed for {path}:\n  {lines}")
    return data


def loads(text: str) -> dict[str, Any]:
    """
    Load and validate an AAIF document from a JSON string.
    Raises ValueError if validation fails.
    """
    data = json.loads(text)
    errors = validate(data)
    if errors:
        lines = "\n  ".join(errors)
        raise ValueError(f"AAIF validation failed:\n  {lines}")
    return data


def info(data: dict[str, Any]) -> dict[str, Any]:
    """
    Return a summary dict of the agent definition.

    Keys: name, goal, sc_version, status, provider, model, tool_count,
          memory_count, roles, capabilities_required, conformance_level.
    """
    agent = data.get("agent", {})
    model = agent.get("model", {})
    orch = agent.get("orchestration", {})

    tool_count = len(agent.get("tools", []))
    memory_count = len(agent.get("memory", []))
    required_caps = agent.get("required_capabilities", [])
    constraints = agent.get("constraints", [])

    # Infer conformance level heuristically
    level = "Core"
    if tool_count > 0 and any(
        t.get("parameters_schema") for t in agent.get("tools", [])
    ):
        level = "Tooled"
    if constraints:
        level = "Portable"
    if orch.get("role") in ("orchestrator", "router"):
        level = "Multi-agent"
    compliance = agent.get("compliance", {})
    telemetry = agent.get("telemetry", {})
    evaluation = agent.get("evaluation", {})
    if telemetry.get("tracing") and evaluation.get("metrics"):
        level = "Observable"
    if compliance.get("audit_log") and compliance.get("safety_level") in ("strict", "regulated"):
        level = "Enterprise"
    if required_caps and any("state." in c for c in required_caps):
        level = "Stateful"

    return {
        "name": agent.get("name"),
        "goal": agent.get("goal"),
        "sc_version": data.get("sc_version", "unknown"),
        "status": data.get("status", "active"),
        "provider": model.get("provider"),
        "model": model.get("preferred"),
        "tool_count": tool_count,
        "memory_count": memory_count,
        "roles": [orch.get("role")] if orch.get("role") else [],
        "capabilities_required": required_caps,
        "conformance_level": level,
    }
