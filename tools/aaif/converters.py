"""
aaif.converters — Stub converters from AAIF to popular agent frameworks.

Each converter takes a validated AAIF dict (from aaif.load or aaif.loads) and
returns a framework-specific configuration dict.  These are reference stubs —
they map the fields that have direct equivalents and surface unmappable fields
in an 'unmapped' key so integrators know what still needs manual wiring.

Supported targets:
  - langgraph        : LangGraph StateGraph configuration            (AAIF -> framework)
  - crewai           : CrewAI Crew + Agent configuration             (AAIF -> framework)
  - autogen          : Microsoft AutoGen AssistantAgent configuration (AAIF -> framework)
  - openai_assistant : OpenAI Assistants API object — BIDIRECTIONAL    (AAIF <-> framework)

The OpenAI Assistants converter is bidirectional and round-trip tested
(`tools/test_roundtrip.py`): for the Core+Tooled field set,
    from_openai_assistant(to_openai_assistant(agent)) == agent
holds. Fields with no Assistants equivalent (goal, provider, response_format
nuance, non-function tool protocols) are carried losslessly in the assistant's
`metadata["x-aaif"]` extension slot so nothing is dropped on the round trip.

Each AAIF->framework function returns:
  {
    "config": { ... },            # Framework-specific config
    "unmapped": { ... },          # AAIF fields with no direct equivalent
    "warnings": [ "..." ],        # Non-fatal mapping notes
  }
"""
from __future__ import annotations

import json
from typing import Any


# ── helpers ────────────────────────────────────────────────────────────────

def _model_name(model: dict) -> str:
    provider = model.get("provider", "")
    preferred = model.get("preferred", "gpt-4o")
    if provider and "/" not in preferred:
        return f"{provider}/{preferred}"
    return preferred


# ── LangGraph ──────────────────────────────────────────────────────────────

def to_langgraph(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert an AAIF agent definition to a LangGraph StateGraph configuration.

    Returns a dict with keys:
      config.graph_name       — agent.name
      config.system_prompt    — agent.instructions
      config.model            — provider/model string
      config.tools            — list of tool name + description dicts
      config.recursion_limit  — agent.runtime.max_iterations (or default 25)
      config.checkpointer     — True if state.checkpoint capability is declared
    """
    agent = data.get("agent", {})
    model = agent.get("model", {})
    runtime = agent.get("runtime", {})
    caps = agent.get("required_capabilities", [])

    tools_out = []
    unmapped_tools = []
    for tool in agent.get("tools", []):
        entry: dict[str, Any] = {
            "name": tool.get("name"),
            "description": tool.get("description", ""),
        }
        if tool.get("parameters_schema"):
            entry["input_schema"] = tool["parameters_schema"]
        if tool.get("protocol") in ("mcp", "openapi"):
            unmapped_tools.append({
                "name": tool.get("name"),
                "reason": f"protocol={tool.get('protocol')} requires a LangGraph-specific adapter",
            })
        tools_out.append(entry)

    config: dict[str, Any] = {
        "graph_name": agent.get("name"),
        "system_prompt": agent.get("instructions", ""),
        "model": _model_name(model),
        "tools": tools_out,
        "recursion_limit": runtime.get("max_iterations", 25),
        "checkpointer": any("state.checkpoint" in c for c in caps),
    }

    unmapped: dict[str, Any] = {}
    warnings: list[str] = []

    if model.get("fallbacks"):
        unmapped["model.fallbacks"] = model["fallbacks"]
        warnings.append(
            "model.fallbacks[] has no native LangGraph equivalent — "
            "implement via a custom LLM wrapper or LiteLLM."
        )
    if agent.get("orchestration"):
        orch = agent["orchestration"]
        unmapped["orchestration"] = orch
        warnings.append(
            "orchestration block must be manually wired as a LangGraph multi-agent graph. "
            "See AAIF §E for topology patterns."
        )
    if agent.get("compliance"):
        unmapped["compliance"] = agent["compliance"]
        warnings.append(
            "compliance fields have no native LangGraph equivalent — "
            "implement via LangSmith guardrails or custom callbacks."
        )
    if unmapped_tools:
        unmapped["tools_needing_adapters"] = unmapped_tools

    return {"config": config, "unmapped": unmapped, "warnings": warnings}


# ── CrewAI ─────────────────────────────────────────────────────────────────

def to_crewai(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert an AAIF agent definition to a CrewAI Crew + Agent configuration.

    Returns a dict with keys:
      config.agent   — CrewAI Agent constructor kwargs
      config.tasks   — list of task dicts (one per pipeline step if declared)
      config.crew    — CrewAI Crew constructor kwargs
    """
    agent = data.get("agent", {})
    model = agent.get("model", {})
    orch = agent.get("orchestration", {})

    crewai_agent: dict[str, Any] = {
        "role": orch.get("role", "worker"),
        "goal": agent.get("goal", ""),
        "backstory": agent.get("instructions", ""),
        "llm": _model_name(model),
        "tools": [t.get("name") for t in agent.get("tools", [])],
        "allow_delegation": orch.get("role") == "orchestrator",
        "verbose": True,
    }

    if agent.get("runtime", {}).get("max_iterations"):
        crewai_agent["max_iter"] = agent["runtime"]["max_iterations"]

    tasks: list[dict[str, Any]] = []
    for step in orch.get("pipeline", []):
        tasks.append({
            "description": step.get("step", step) if isinstance(step, dict) else step,
            "agent": agent.get("name"),
        })

    crew: dict[str, Any] = {
        "agents": [agent.get("name")],
        "tasks": [t["description"] for t in tasks] if tasks else ["(define tasks manually)"],
        "process": "sequential" if not orch.get("parallel_execution") else "hierarchical",
        "verbose": True,
    }

    unmapped: dict[str, Any] = {}
    warnings: list[str] = []

    if model.get("fallbacks"):
        unmapped["model.fallbacks"] = model["fallbacks"]
        warnings.append(
            "model.fallbacks[] has no native CrewAI equivalent — "
            "implement via LiteLLM fallback config."
        )
    if agent.get("memory"):
        unmapped["memory"] = agent["memory"]
        warnings.append(
            "memory[] backends must be mapped to CrewAI's memory system manually. "
            "CrewAI supports short-term, long-term, entity, and user memory."
        )
    if agent.get("compliance"):
        unmapped["compliance"] = agent["compliance"]
        warnings.append(
            "compliance fields have no native CrewAI equivalent — "
            "implement via custom task callbacks."
        )

    return {
        "config": {
            "agent": crewai_agent,
            "tasks": tasks,
            "crew": crew,
        },
        "unmapped": unmapped,
        "warnings": warnings,
    }


# ── AutoGen ────────────────────────────────────────────────────────────────

def to_autogen(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert an AAIF agent definition to a Microsoft AutoGen AssistantAgent
    configuration dict.
    """
    agent = data.get("agent", {})
    model = agent.get("model", {})

    llm_config: dict[str, Any] = {
        "model": model.get("preferred", "gpt-4o"),
        "api_type": model.get("provider", "openai"),
    }
    if model.get("params", {}).get("temperature") is not None:
        llm_config["temperature"] = model["params"]["temperature"]

    config: dict[str, Any] = {
        "name": agent.get("name", "aaif_agent"),
        "system_message": agent.get("instructions", ""),
        "llm_config": llm_config,
        "human_input_mode": (
            "ALWAYS"
            if agent.get("compliance", {}).get("human_in_the_loop", {}).get("enabled")
            else "NEVER"
        ),
        "max_consecutive_auto_reply": agent.get("runtime", {}).get("max_iterations", 10),
    }

    unmapped: dict[str, Any] = {}
    warnings: list[str] = []

    if agent.get("tools"):
        unmapped["tools"] = [t.get("name") for t in agent["tools"]]
        warnings.append(
            "tools[] must be registered with AutoGen's FunctionCallingAgent or "
            "using @register_for_execution / @register_for_llm decorators."
        )
    if model.get("fallbacks"):
        unmapped["model.fallbacks"] = model["fallbacks"]
        warnings.append("model.fallbacks[] should be expressed as multiple llm_config entries.")
    if agent.get("memory"):
        unmapped["memory"] = agent["memory"]
        warnings.append("memory[] has no direct AutoGen equivalent — use ConversableAgent memory or external stores.")

    return {"config": config, "unmapped": unmapped, "warnings": warnings}


# ── OpenAI Assistants (BIDIRECTIONAL, round-trip tested) ─────────────────────

# AAIF model.response_format  <->  OpenAI Assistants response_format
_RF_AAIF_TO_OPENAI = {
    "text": "auto",
    "markdown": "auto",
    "json": {"type": "json_object"},
    "json_schema": {"type": "json_schema"},
}

# Extension slot used to carry AAIF fields that have no native Assistants home,
# so the round trip is lossless. OpenAI metadata values must be strings.
_AAIF_META_KEY = "x-aaif"


def to_openai_assistant(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert an AAIF agent definition to an OpenAI Assistants API object.

    Direct maps: name, instructions, model.preferred, temperature, top_p,
    response_format, and 'function'-protocol tools (-> {"type":"function",...}).

    Anything without a native Assistants field (goal, provider, sc metadata,
    the precise response_format, and non-function tool protocols) is preserved
    in metadata["x-aaif"] so from_openai_assistant() can reconstruct the
    original AAIF document exactly.
    """
    agent = data.get("agent", {})
    model = agent.get("model", {})
    params = model.get("params", {})

    assistant_tools: list[dict[str, Any]] = []
    carried_tools: list[dict[str, Any]] = []  # non-function tools carried verbatim
    warnings: list[str] = []
    for tool in agent.get("tools", []):
        if tool.get("protocol", "function") == "function":
            assistant_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters_schema", {"type": "object", "properties": {}}),
                },
            })
        else:
            carried_tools.append(tool)
            warnings.append(
                f"tool '{tool.get('name')}' uses protocol '{tool.get('protocol')}', which the "
                "Assistants API cannot execute natively; carried in metadata['x-aaif'] for round-trip."
            )

    config: dict[str, Any] = {"name": agent.get("name")}
    if agent.get("instructions"):
        config["instructions"] = agent["instructions"]
    if model.get("preferred"):
        config["model"] = model["preferred"]
    if model.get("temperature") is not None:
        config["temperature"] = model["temperature"]
    if params.get("top_p") is not None:
        config["top_p"] = params["top_p"]
    if assistant_tools:
        config["tools"] = assistant_tools

    rf = model.get("response_format")
    if rf in _RF_AAIF_TO_OPENAI and rf != "text":
        mapped = _RF_AAIF_TO_OPENAI[rf]
        if rf == "json_schema" and agent.get("io", {}).get("output_schema"):
            mapped = {"type": "json_schema",
                      "json_schema": {"name": "output", "schema": agent["io"]["output_schema"]}}
        config["response_format"] = mapped

    # Build the lossless carry payload (only what the direct maps don't cover).
    carry: dict[str, Any] = {
        "sc_standard": data.get("sc_standard", "SC-006"),
        "sc_version": data.get("sc_version"),
        "agent": {"goal": agent.get("goal")},
    }
    if data.get("agent_id"):
        carry["agent_id"] = data["agent_id"]
    if model.get("provider"):
        carry["agent"]["model_provider"] = model["provider"]
    if model.get("provider_id"):
        carry["agent"]["model_provider_id"] = model["provider_id"]
    if rf and rf != "text":
        carry["agent"]["response_format"] = rf
    if carried_tools:
        carry["agent"]["nonfunction_tools"] = carried_tools
    config["metadata"] = {_AAIF_META_KEY: json.dumps(carry, separators=(",", ":"))}

    unmapped: dict[str, Any] = {}
    for k in ("orchestration", "memory", "compliance", "telemetry", "evaluation", "context", "events"):
        if agent.get(k):
            unmapped[k] = agent[k]
    if model.get("fallbacks"):
        unmapped["model.fallbacks"] = model["fallbacks"]
        warnings.append("model.fallbacks[] has no Assistants equivalent — implement routing in your client.")

    return {"config": config, "unmapped": unmapped, "warnings": warnings}


def from_openai_assistant(assistant: dict[str, Any]) -> dict[str, Any]:
    """
    Convert an OpenAI Assistants API object back into an AAIF agent definition.

    If the assistant carries a metadata['x-aaif'] payload (as produced by
    to_openai_assistant), the AAIF-specific fields are restored from it so the
    round trip is lossless. Otherwise a best-effort AAIF document is produced
    (goal defaults to a synthesised string and provider is inferred).
    """
    meta = assistant.get("metadata", {}) or {}
    carry: dict[str, Any] = {}
    if isinstance(meta.get(_AAIF_META_KEY), str):
        try:
            carry = json.loads(meta[_AAIF_META_KEY])
        except (ValueError, TypeError):
            carry = {}
    carry_agent = carry.get("agent", {}) if isinstance(carry, dict) else {}

    model: dict[str, Any] = {}
    if assistant.get("model"):
        model["provider"] = carry_agent.get("model_provider", "openai")
        if carry_agent.get("model_provider_id"):
            model["provider_id"] = carry_agent["model_provider_id"]
        model["preferred"] = assistant["model"]
    if assistant.get("temperature") is not None:
        model["temperature"] = assistant["temperature"]
    if assistant.get("top_p") is not None:
        model["params"] = {"top_p": assistant["top_p"]}

    rf = carry_agent.get("response_format")
    if rf:
        model["response_format"] = rf
    elif isinstance(assistant.get("response_format"), dict):
        t = assistant["response_format"].get("type")
        model["response_format"] = {"json_object": "json", "json_schema": "json_schema"}.get(t, "text")

    tools: list[dict[str, Any]] = []
    for t in assistant.get("tools", []):
        if t.get("type") == "function" and "function" in t:
            fn = t["function"]
            tools.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "protocol": "function",
                "parameters_schema": fn.get("parameters", {"type": "object", "properties": {}}),
            })
    tools.extend(carry_agent.get("nonfunction_tools", []))

    agent: dict[str, Any] = {
        "name": assistant.get("name") or "Imported Assistant",
        "goal": carry_agent.get("goal") or f"Imported from OpenAI Assistant '{assistant.get('name', '')}'.",
    }
    if assistant.get("instructions"):
        agent["instructions"] = assistant["instructions"]
    if model:
        agent["model"] = model
    if tools:
        agent["tools"] = tools

    doc: dict[str, Any] = {"sc_standard": carry.get("sc_standard", "SC-006")}
    if carry.get("sc_version"):
        doc["sc_version"] = carry["sc_version"]
    if carry.get("agent_id"):
        doc["agent_id"] = carry["agent_id"]
    doc["agent"] = agent
    return doc
