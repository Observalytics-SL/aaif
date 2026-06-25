# SC-006 · AAIF — Autonomous Agent Interchange Format

[![Schema Commons Standard](assets/schema-commons-badge.svg)](https://github.com/Observalytics-SL) ![Draft 3.4](https://img.shields.io/badge/status-draft%203.4-orange) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20845316.svg)](https://doi.org/10.5281/zenodo.20845316) [![Cite](https://img.shields.io/badge/cite-CITATION.cff-blue)](CITATION.cff)

> **Portable AI agents.** ChatGPT, Claude, Gemini, Cline, Continue, Open WebUI, LangGraph, CrewAI, AutoGen — every platform invents its own agent format. AAIF is the "Agent Common Information Model": define an agent once, run it anywhere.

## The problem

An agent you build in one tool is trapped there. Goals, tools, memory, guardrails, provider routing, and orchestration topology are all expressed differently per vendor — so there's no portability and no shared library of agents.

## The solution

A single, vendor-neutral agent definition covering the full lifecycle of a production multi-agent system:

```json
{
  "agent_id": "...",
  "agent": {
    "goal": "...",
    "model": { "provider": "anthropic", "preferred": "claude-opus-4-5", "fallbacks": [...] },
    "orchestration": { "role": "orchestrator", "subagents": [...], "parallel_execution": true },
    "context": [...],
    "tools": [...],
    "memory": [...],
    "constraints": [...],
    "runtime": { "timeout_seconds": 300 },
    "telemetry": { "tracing": true },
    "evaluation": { "judge_model": "gpt-4o", "metrics": [...] },
    "compliance": { "safety_level": "strict", "data_residency": "EU" }
  }
}
```

Aligned with OpenAI/Anthropic/Gemini function-calling, Model Context Protocol (MCP), OpenTelemetry, and W3C PROV.

## Status & honest expectations

AAIF is an **early-stage draft standard with no external adopters yet**. "Run anywhere" is the design goal, not a claim about today — true cross-runtime portability depends on other platforms implementing it, which hasn't happened yet. The concrete near-term value is real and available now:

- a clean, versioned **export/import format** for your own agent library, so agents aren't trapped in one tool;
- **dogfooding** on a reference runtime (the first runtime to implement AAIF is listed as the reference in [ADOPTERS.md](ADOPTERS.md));
- **first-adopter credibility** if you help shape the spec early.

Two known design trade-offs are documented rather than hidden: routing/handoff conditions can be natural-language hints (non-deterministic — prefer the structured forms in [§V](SPECIFICATION.md)), and full **Stateful** conformance (live migration, streaming handoff) is large — most implementations should target **Enterprise** first.

## What's new in v2.1 and v3

| Area | v1 | v2 | v2.1 | v3 |
|------|----|----|------|-----|
| LLM routing | Single model | Fallbacks + routing | ← | ← |
| Multi-agent | — | All topologies | ← | ← |
| Tool auth | — | `env_var` | **`vault_ref`** (5 providers) | ← |
| Capability negotiation | — | — | **`required_capabilities[]`** | ← |
| Provider params | Standard fields | Standard fields | **`params.extended`** pass-through | ← |
| Agent state | — | — | — | **`agent-state.schema.json`** |
| Live migration | — | — | — | **7-step migration protocol** |
| Streaming handoff | — | — | — | **NDJSON wire format (§S)** |

## Multi-agent topology patterns

```
1. Sequential pipeline      [A] → [B] → [C] → [D]

2. Parallel swarm           [Orchestrator]─┬─[Worker A]─┐
   (fan-out / fan-in)                      ├─[Worker B]─┤─[Synthesizer]
                                           └─[Worker C]─┘

3. Dynamic routing          [Router]─when:X──→[Specialist A]
                                    ─when:Y──→[Specialist B]

4. Mid-run handoff          [Agent A]─condition──→[Agent B]
```

## LLM provider support

AAIF supports 16 providers out of the box: `openai`, `anthropic`, `google`, `vertex_ai`, `mistral`, `cohere`, `groq`, `ollama`, `azure_openai`, `bedrock`, `huggingface`, `together`, `fireworks`, `deepseek`, `xai`, `openrouter`. Anything else — GitHub Copilot, Cline-routed endpoints, self-hosted LiteLLM/vLLM gateways — uses `provider: "custom"` with `provider_id` + `base_url` (no enum churn). Set `model.routing_strategy` to `cost`, `latency`, `quality`, or `round_robin` for platform-level optimisation.

## An open standard, not just a schema

AAIF is built to be adopted, extended, and cited by anyone — without asking permission and without forking:

- **Extend without forking.** Open extension points (providers, capabilities, condition languages, vault providers, memory backends, tool protocols) live in community [`registries/`](registries/) with IANA-style registration policies. Add an identifier by pull request; no schema version bump. The schema enums are just a *recommended subset*. See [SPECIFICATION §X](SPECIFICATION.md).
- **Verify conformance.** Self-certify per level and direction against the public test suite and publish a machine-readable report at `/.well-known/aaif-conformance.json`. See [CONFORMANCE.md](CONFORMANCE.md).
- **Prove portability.** The reference `aaif` package converts agents to and from OpenAI Assistants, with one-way exporters for LangGraph / CrewAI / AutoGen.
- **Cite it.** [`CITATION.cff`](CITATION.cff) + a Zenodo DOI; see [PUBLISHING.md](PUBLISHING.md) for the arXiv / IETF Internet-Draft / W3C Community Group paths.
- **Report issues safely.** [SECURITY.md](SECURITY.md) defines the threat model and disclosure process.

```bash
# validate, convert, import
PYTHONPATH=tools python -m aaif validate examples/invoice-chaser.json
PYTHONPATH=tools python -m aaif convert  examples/invoice-chaser.json --target openai_assistant
PYTHONPATH=tools python -m aaif import   my-assistant.json --source openai_assistant
python tools/validate.py
```

## Who benefits

| Role | Benefit |
|------|---------|
| **Platform builders** | Import/export agents across runtimes (LangGraph ↔ CrewAI ↔ AutoGen) without re-writing |
| **Enterprise teams** | Enforce compliance (`data_residency`, PII handling, audit log) declaratively |
| **DevOps / MLOps** | CI/CD gates using `evaluation.test_cases[]` and LLM-as-judge scoring |
| **Developers** | Share and reuse agents from a common library with full context |
| **Open-source communities** | Build a vendor-neutral ecosystem of production-grade agents |

## Files

| File | Description |
|------|-------------|
| [SPECIFICATION.md](SPECIFICATION.md) | Full specification: terminology (RFC 2119), field dictionary, topology, conditions (§V), extension registries (§X), conformance (§Y), references (§Z) |
| [WHITEPAPER.md](WHITEPAPER.md) | Publication essay — the case for a portable agent standard and readiness assessment |
| [ABSTRACT.md](ABSTRACT.md) | Structured abstract for registry submission, IETF I-D, and citation |
| [CONFORMANCE.md](CONFORMANCE.md) | How to self-certify a platform and publish a conformance report |
| [PUBLISHING.md](PUBLISHING.md) | Paths to DOI, arXiv, IETF Internet-Draft, and W3C Community Group |
| [SECURITY.md](SECURITY.md) | Threat model and vulnerability disclosure policy |
| [CITATION.cff](CITATION.cff) | Citation metadata (GitHub "Cite this repository" + Zenodo DOI) |
| [registries/](registries/) | Community extension registries (providers, capabilities, condition langs, vaults, backends, protocols) |
| [CHANGELOG.md](CHANGELOG.md) | Version history and roadmap |
| [ADOPTERS.md](ADOPTERS.md) | Self-service adopter and implementation registry |
| [schema/conformance-report.schema.json](schema/conformance-report.schema.json) | JSON Schema — platform conformance self-certification report |
| [schema/platform-manifest.schema.json](schema/platform-manifest.schema.json) | JSON Schema — platform capability manifest |
| [schema/agent.schema.json](schema/agent.schema.json) | JSON Schema (draft 2020-12) — agent definition (sc_version 3.4.0) |
| [schema/agent-state.schema.json](schema/agent-state.schema.json) | JSON Schema (draft 2020-12) — agent state checkpoint (sc_version 3.4.0) |
| [context.jsonld](context.jsonld) | JSON-LD context mapping all AAIF terms to URIs (schema.org, PROV-O, Dublin Core, AAIF vocab) |
| [examples/invoice-chaser.json](examples/invoice-chaser.json) | Worker agent: AR automation with MCP tool, Redis + Postgres memory, EU compliance |
| [examples/research-summarizer.json](examples/research-summarizer.json) | Worker agent: web research with multi-provider fallbacks, Qdrant vector memory, evaluation |
| [examples/orchestrator-pipeline.json](examples/orchestrator-pipeline.json) | Orchestrator: sequential 4-agent BI pipeline with human-in-the-loop |
| [examples/code-review-swarm.json](examples/code-review-swarm.json) | Orchestrator: parallel 3-reviewer swarm with consensus + synthesizer |
| [examples/invoice-chaser-checkpoint.json](examples/invoice-chaser-checkpoint.json) | Agent State: Invoice Chaser mid-run checkpoint in `awaiting_approval` status |

## Validate

```bash
python tools/validate.py
```

## Quick start: importing an agent

```python
import json, jsonschema, requests

# 1. Load an AAIF definition
with open("examples/invoice-chaser.json") as f:
    agent_def = json.load(f)

# 2. Validate against the schema
schema = json.load(open("schema/agent.schema.json"))
jsonschema.validate(agent_def, schema)

# 3. Extract what your platform needs
agent = agent_def["agent"]
primary_model   = f"{agent['model']['provider']}/{agent['model']['preferred']}"
fallback_chain  = [(f["provider"], f["model"]) for f in agent["model"].get("fallbacks", [])]
tools           = agent.get("tools", [])
constraints     = agent.get("constraints", [])
runtime_timeout = agent.get("runtime", {}).get("timeout_seconds", 120)
```

## Conformance levels

| Level | Requirements |
|-------|-------------|
| **Core** | Valid schema; `name` + `goal` present |
| **Tooled** | Core + ≥1 tool with `parameters_schema` |
| **Portable** | Tooled + `constraints[]` + resolvable endpoints |
| **Multi-agent** | Portable + `orchestration.role` + subagents or handoff |
| **Observable** | Portable + tracing enabled + ≥1 evaluation metric |
| **Enterprise** | Observable + compliance declared + audit log + signature |
| **Stateful** *(advanced)* | Enterprise + `required_capabilities[]` declared + `state.checkpoint` capability + Agent State checkpoints supported |

> **Pick a target, don't climb to the top.** Most of AAIF's value lands at **Portable → Enterprise** (all expressible in `agent.schema.json`). **Stateful** is a separate advanced tier covering v3 live state, migration, and streaming handoff — adopt it only when live pause/resume or cross-runtime migration is an actual requirement. See [SPECIFICATION §M](SPECIFICATION.md).

## 📣 Ready-to-post LinkedIn announcement

> Your AI agent is trapped in one platform.
>
> Every LLM framework — LangGraph, CrewAI, AutoGen, Open WebUI, Cline — stores agents differently. So every agent you build is a silo.
>
> We just published **AAIF (SC-006) v3.4** — the open "Agent Common Information Model" for multi-agent LLM platforms.
>
> Covers: multi-provider routing with fallbacks (16 providers), parallel swarm + pipeline topologies, tool auth, vector memory backends, OpenTelemetry, LLM-as-judge evaluation, enterprise compliance (GDPR residency, PII handling, audit log, HITL), and live agent state migration across runtimes.
>
> Define an agent once. Run it on any runtime. Share it in a common library.
>
> Part of **Schema Commons** — the Creative Commons for data schemas.
>
> #AIagents #MultiAgent #MCP #OpenStandards #SchemaCommons #LLM #LangGraph #CrewAI #AutoGen

## Companion standards

| Standard | What it adds |
|----------|-------------|
| [ACPM — SC-014](https://github.com/Observalytics-SL/acpm) | Capability profiles: what an agent, platform, tool, or model *offers* — trust, cost, SLA, delegation |
| [AREG — SC-013](https://github.com/Observalytics-SL/areg) | Agent registry: how to publish and discover AAIF agents |

*Licensed CC BY 4.0 — part of [Schema Commons](https://github.com/Observalytics-SL).*
