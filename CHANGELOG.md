# SC-006 AAIF — Changelog

All notable changes to the Autonomous Agent Interchange Format are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

A **MAJOR** version increment means an incompatible schema change (field removed, type changed, enum value removed).
A **MINOR** version increment means a backwards-compatible addition (new optional field or enum value).
A **PATCH** version increment means clarifications, documentation fixes, or non-normative example changes.

---

## [3.4.0] — 2026-06-11

Backward-compatible (MINOR). Turns AAIF from a well-specified schema into a **publishable, community-governed open standard**: extensible without forking, verifiably conformant, and proven to round-trip.

### Added

**Extension registries (SPECIFICATION §X)** — six machine-readable registries under [`registries/`](registries/) (`providers`, `capabilities`, `condition-languages`, `vault-providers`, `memory-backends`, `tool-protocols`), each validated by `registries/registry.schema.json`. The schema enums are now an explicit *recommended subset* of the registries; new providers/backends/etc. are added by PR with IANA-style registration policies (Specification Required / Expert Review / Standards Action) and a `provisional → standard` status lifecycle — **no schema version bump required**. This is the standard's open-extension mechanism (the "IANA Considerations").

**Conformance self-certification program (SPECIFICATION §Y, [CONFORMANCE.md](CONFORMANCE.md))** — per-level, per-direction (`producer`/`consumer`/`both`) self-certification against the public test corpus. New `schema/conformance-report.schema.json` + `examples/conformance-report.json`, published at `/.well-known/aaif-conformance.json`, with a behavioural enforcement checklist per level.

**Bidirectional interoperability + proof** — `aaif.converters.to_openai_assistant` / `from_openai_assistant` (OpenAI Assistants API), with unmapped AAIF fields carried losslessly in `metadata["x-aaif"]`. New `tools/test_roundtrip.py` proves `from(to(agent)) == agent` for the Core+Tooled field set. CLI gains `convert --target openai_assistant` and a new `import --source openai_assistant` command.

**Publication scaffolding (PhD/standards track)** — `CITATION.cff` (GitHub citation + Zenodo DOI), `SECURITY.md` (threat model + disclosure policy), `PUBLISHING.md` (DOI / arXiv / IETF Internet-Draft / W3C CG paths). SPECIFICATION gains a **Conventions & Terminology** section (RFC 2119/8174) and a **§Z References** section (normative + informative).

### Changed

- `x-sc-version` → `3.4.0` on all schemas; `agent.schema.json` `sc_version` default → `3.4.0`; SPECIFICATION header → 3.4.0.
- `aaif.validate()` now defaults to `agent.schema.json` when no `x-sc-schema` is given, instead of the first file alphabetically (sibling schema files no longer shadow the agent schema).
- `tools/validate.py` already strips annotation keys; round-trip and registry suites added to the test toolchain.

### Tests

- New suites: `tools/test_registries.py` (registry ↔ schema-enum consistency, 19 checks) and `tools/test_roundtrip.py` (interop round-trip, 21 checks). Existing conformance (16) and example validation (7) unchanged and green.

---

## [3.3.0] — 2026-06-11

Backward-compatible (MINOR). Formalises an extension namespace so AAIF documents can carry vendor/tool metadata and validator hints without breaking strict validation — closing the gap where the conformance fixtures relied on out-of-band key-stripping.

### Added

**Reserved extension namespace (SPECIFICATION §W)** — at the document root of all three schemas (`agent`, `agent-state`, `platform-manifest`):
- `patternProperties` `^x-` — any `x-`-prefixed property is a vendor/tool extension key. Conforming runtimes MUST ignore unknown extension keys and MUST NOT let them alter behaviour. The validator hint `x-sc-schema` now lives legitimately in this namespace.
- a root `_comment` (string) property — a non-normative human annotation, ignored by runtimes.
- New §W with normative rules (ignore-unknown, no-reject-on-extension, preserve-on-passthrough, no behaviour-smuggling) and clarification that `x-sc-schema`/`_comment` stripping is now an optimisation, not a correctness requirement.

### Changed

- `x-sc-version` bumped to `3.3.0` on all three schemas; `agent.schema.json` `sc_version` default → `3.3.0`. (Agent-state instance `sc_version` semantics unchanged — the state format itself did not change.)
- SPECIFICATION header → 3.3.0; added §W.
- `tools/validate.py` now also strips `_comment` (matching `tools/test_conformance.py`) so the two validators behave identically and older pinned schemas still validate.

### Tests

- Conformance suite unchanged and still 16/16. With the extension namespace, every must-pass fixture now validates **directly** (no key-stripping needed), and every must-reject fixture rejects for its **real** rule violation regardless of whether annotation keys were stripped first — removing the false-confidence risk where an invalid fixture could have rejected merely on its `_comment`/`x-sc-schema` key.

---

## [3.2.0] — 2026-06-11

Backward-compatible (MINOR). Addresses two documented design caveats: non-deterministic NL routing fields, and provider-enum gaps.

### Added

**Structured `Condition` type (SPECIFICATION §V)** — a shared, deterministic form for the four control-flow fields that were previously free strings: `orchestration.subagents[].when`, `orchestration.handoff[].condition`, `events.triggers[].filter`, and `compliance.human_in_the_loop.trigger`. A Condition is now either:
- a structured object `{ "lang", "expr", "nl" }` where `lang` ∈ `jsonpath` / `jmespath` / `cel` / `jsonlogic` / `always` / `never` — evaluated deterministically and identically across runtimes (RECOMMENDED), or
- a bare string — now explicitly demoted to an advisory natural-language hint that MUST NOT be relied on for portable routing.

`expr` is required for the expression languages and omitted for `always`/`never`. The optional `nl` carries a human description. New normative rules cover unsupported-`lang` handling (tied to `safety_level`, mirroring `required_capabilities`) and a portability warning for string conditions.

**Provider extensibility** — closes the enum gap for providers like GitHub Copilot, Cline-routed endpoints, OpenRouter, and self-hosted gateways:
- Added `openrouter` and `vertex_ai` to the `model.provider` enum.
- Added `model.provider_id` (string) — **required** when `provider: "custom"` — so custom providers route deterministically without a dedicated enum value.
- Added `model.base_url` (uri) — endpoint for self-hosted/gateway/OpenAI-compatible providers.

### Changed

- Schema `x-sc-version` and default `sc_version` → `3.2.0`.
- SPECIFICATION header → 3.2.0; added §V; added a **Stateful (advanced)** row and conformance-scope guidance to §M (Enterprise is the recommended primary target; Stateful is opt-in).
- README: provider list updated to 16 + custom escape hatch; added an honest "Status & expectations" section (no external adopters yet; near-term value is export/import + dogfooding + first-adopter credibility).

### Tests

- New must-pass fixtures: `structured-conditions.json`, `custom-provider.json`.
- New must-reject fixtures: `bad-condition-lang.json`, `condition-missing-expr.json`, `custom-provider-no-id.json`.
- Existing examples migrated deterministic filters/`when`s to the structured form (string forms retained where genuinely advisory).

---

## [3.0.0] — 2026-06-10

### Added

**New companion schema: `schema/agent-state.schema.json`**

Agent State documents capture a complete, portable snapshot of a running agent and enable three use cases: pause/resume, cross-platform live migration, and crash recovery. This is a separate schema file (not an extension of agent.schema.json) with its own `sc_version: "3.0.0"`.

Key fields added:
- `state_id` (uuid) — unique checkpoint identifier; new UUID per capture
- `run_id` (uuid) — groups all checkpoints for one execution run
- `agent_id` / `agent_version` — link to the originating agent definition
- `checkpoint_at` (datetime) — UTC capture timestamp
- `status` (enum) — `running` / `paused` / `awaiting_approval` / `awaiting_tool_result` / `completed` / `failed` / `migrating`
- `iteration` (integer) — current loop count; enforced against `max_iterations` on restore
- `pipeline_position` — `{current_step, completed_steps[], remaining_steps[], current_subagent, parallel_slot}`
- `conversation[]` — full message history with `{role, content, tool_call_id, tool_name, token_count, timestamp}`
- `memory_snapshot[]` — all in-scope memory items with `ttl_remaining_seconds` (embeddings NOT serialised — re-computed on restore)
- `pending_tool_calls[]` — in-flight/queued tool calls with `callback_url` for async resume
- `subagent_states[]` — per-subagent summaries enabling deep multi-agent migration
- `variables` — task-scope named variables (free-form key-value)
- `approval_request` — present when `status = "awaiting_approval"`; contains pending action and approver hint
- `error` — present when `status = "failed"`; contains code, message, step, retries_remaining
- `provenance.checksum` — SHA-256 of the canonical JSON; receiving platform MUST verify before restoring
- `provenance.migration_token` — short-lived signed token for authorising cross-platform transfers

**New SPECIFICATION.md sections:**
- §Q: Agent State & Checkpointing — full field dictionary and 7-step migration protocol
- §R: Capability Negotiation — standard capability vocabulary and per-safety-level platform behaviour
- §S: Streaming Handoff Wire Format — `application/x-aaif-handoff+ndjson` protocol with 8 message types

**New example:**
- `examples/invoice-chaser-checkpoint.json` — a real checkpoint of the Invoice Chaser agent mid-run, in `awaiting_approval` status with drafted emails in memory

---

## [2.1.0] — 2026-06-10

### Added

- **`tools[].auth.vault_ref`** — reference to a secret in an external vault. Fields: `{provider, path, key, version}`. Providers: `aws_secretsmanager`, `hashicorp_vault`, `azure_keyvault`, `gcp_secretmanager`, `1password`, `custom`. Takes precedence over `env_var` if both are specified. The vault value is resolved at execution time; it is never stored in the AAIF document.
- **`agent.required_capabilities[]`** — array of dot-namespaced capability strings the agent requires from its executing runtime (e.g. `"tool.mcp"`, `"memory.vector"`, `"orchestration.parallel"`, `"auth.vault"`, `"state.checkpoint"`). A platform MUST reject or warn if any declared capability is unsupported. Full vocabulary defined in SPECIFICATION.md §R.
- **`model.params.extended`** — provider-specific sampling parameters pass-through object. `additionalProperties: true`. Forwards verbatim to the provider's API (e.g. Anthropic extended thinking config, Google safety settings). Enables platform-specific features without breaking the schema.

### Changed

- `x-sc-version` in `agent.schema.json` updated to `"2.1.0"`
- Default `sc_version` updated to `"2.1.0"`
- `auth` description updated to mention vault resolution
- All examples updated to `sc_version: "2.1.0"`

### Removed (none — full backward compatibility maintained)

All v1 and v2.0 documents continue to validate against the v2.1 schema.

---

## [2.0.0] — 2026-06-10

### Added

**Root-level fields:**
- `agent_id` (string, uuid) — globally unique stable identifier; preserved on import/export
- `status` (enum: draft/active/deprecated) — lifecycle state
- `tags` (string[]) — labels for routing, search, and capability filtering

**agent.model:**
- `provider` (enum, 14 providers) — primary LLM provider identifier
- `fallbacks[]` — ordered fallback chain of `{provider, model, max_cost_usd_per_1k_tokens}`
- `routing_strategy` (enum) — `preferred_first` / `cost` / `latency` / `quality` / `round_robin`
- `params` — sampling parameters: `max_tokens`, `top_p`, `frequency_penalty`, `presence_penalty`, `stop`, `seed`
- `response_format` (enum) — `text` / `json` / `json_schema` / `markdown`

**agent.orchestration (new block):**
- `role` (enum) — `orchestrator` / `worker` / `evaluator` / `router` / `synthesizer`
- `subagents[]` — child agent references with `ref` (UUID/URI), `alias`, `role`, `when`, `pass_memory_keys`
- `handoff[]` — mid-run delegation rules with `condition`, `target_agent`, `pass_context`, `pass_memory`
- `pipeline[]` — ordered subagent aliases for sequential execution
- `parallel_execution` (boolean) — fan-out swarm mode
- `max_iterations` (integer) — agentic loop guard, default 10
- `consensus` — `{strategy, min_votes, referee_agent}` for resolving parallel output conflicts

**agent.context[].items:**
- `description` — why this context item is needed
- `refresh_ttl_seconds` — re-fetch interval for `url` type contexts

**agent.tools[].items:**
- `output_schema` — JSON Schema for tool responses
- `auth` — `{type, env_var, header, scopes, token_url}` for bearer/api_key/oauth2/aws_sigv4
- `cache_ttl_seconds` — response cache duration
- `timeout_seconds` — per-tool call timeout
- `rate_limit` — `{requests_per_minute, tokens_per_minute}`
- `name` now has pattern validation `^[a-zA-Z_][a-zA-Z0-9_-]{0,63}$`

**agent.memory[].items:**
- `backend` (enum, 8 options) — `in_memory` / `redis` / `postgres` / `sqlite` / `pinecone` / `weaviate` / `qdrant` / `chroma` / `custom`
- `ttl_seconds` — memory item expiry
- `embedding_model` — model for vector backends
- `retrieval_strategy` (enum) — `similarity` / `keyword` / `hybrid` / `recency`
- `top_k` — retrieved items per query

**agent.io:**
- `streaming` (boolean)
- `format` (enum) — `text` / `json` / `markdown` / `structured`
- `mode` (enum) — `sync` / `async` / `batch`

**agent.events (new block):**
- `triggers[]` — `{type, schedule, event_name, webhook_path, filter}` with types: `manual` / `schedule` / `webhook` / `message` / `event` / `agent_handoff` / `file_change`
- `on_start`, `on_complete`, `on_error`, `on_tool_call` — lifecycle hooks

**agent.runtime (new block):**
- `timeout_seconds`, `max_retries`, `retry_backoff`, `concurrency`, `streaming`, `async_execution`, `queue`, `environment`

**agent.telemetry (new block):**
- `tracing`, `log_level`, `metrics`, `trace_context_header`, `otlp_endpoint`

**agent.evaluation (new block):**
- `judge_model`, `metrics[]` (9 standard metric types with thresholds), `test_cases[]`

**agent.compliance (new block):**
- `safety_level`, `data_residency`, `pii_handling`, `audit_log`, `human_in_the_loop`

**agent:**
- `version` (semver) — agent definition version, independent of schema version
- `skills[]` — capability tags for routing and discovery

**provenance:**
- `updated_at` — last-modified timestamp
- `license` — SPDX license identifier
- `sc_refs[]` — dependencies on other Schema Commons standards

**examples:**
- `examples/orchestrator-pipeline.json` — sequential 4-agent BI pipeline orchestrator
- `examples/code-review-swarm.json` — parallel 3-reviewer swarm with consensus

**documentation:**
- `WHITEPAPER.md` — publication essay and standards readiness assessment
- `ABSTRACT.md` — structured abstract for registries, IETF I-D, and citation
- `ADOPTERS.md` — self-service adopter registry
- `CHANGELOG.md` — this file
- Enriched `context.jsonld` with full vocabulary mapping (schema.org, PROV-O, Dublin Core, AAIF vocab)

### Changed

- `sc_version` default updated from `"1.0.0"` to `"2.0.0"`
- All existing examples updated to v2 with enriched fields

### Removed (none — full backward compatibility maintained)

All v1 fields remain valid. A v1 document continues to validate against the v2 schema.

---

## [1.0.0] — 2026-06-09

### Added

Initial public draft.

- `sc_standard`, `sc_version`
- `agent.name`, `agent.goal`, `agent.description`, `agent.instructions`
- `agent.model` — `preferred`, `min_context_tokens`, `temperature`
- `agent.context[]` — types: `text`, `file`, `url`, `dataset`, `schema_ref`
- `agent.tools[]` — `name`, `description`, `protocol` (function/mcp/http/openapi), `parameters_schema`, `endpoint`
- `agent.memory[]` — `scope` (user/session/task/long_term), `key`, `content`
- `agent.constraints[]`
- `agent.io` — `input_schema`, `output_schema`
- `provenance` — `authored_by`, `source_platform`, `created_at`, `signature`
- `context.jsonld` — basic vocabulary mapping
- `examples/invoice-chaser.json`, `examples/research-summarizer.json`

---

## [3.1.0] — 2026-06-10

### Added

**New schema: `schema/platform-manifest.schema.json`**

Platforms that accept AAIF agent definitions may now publish a machine-readable Platform Manifest advertising their runtime capabilities. Enables pre-dispatch capability negotiation between orchestrators and target runtimes.

Key blocks:
- `platform.aaif_conformance_level` — declared conformance level (`Core` … `Stateful`)
- `platform.aaif_versions_supported[]` — list of AAIF sc_version values accepted
- `platform.capabilities.tool.*` — supported protocols and parallel call support
- `platform.capabilities.memory.*` — available backends
- `platform.capabilities.model.providers[]` / `routing_strategies[]`
- `platform.capabilities.orchestration.*` — topologies and `max_subagents`
- `platform.capabilities.auth.vault.providers[]` — which vault providers the platform resolves (resolves the vault capability advertisement gap from Appendix B)
- `platform.capabilities.state.*` — checkpoint, live migration, streaming handoff
- `platform.capabilities.compliance.data_residency_regions[]`
- `platform.intake_endpoint` — optional REST intake URL for POSTing agent definitions

See `examples/platform-manifest.json` for a full example. SPECIFICATION.md §U for the discovery and negotiation protocol.

**Conformance test suite: `tests/conformance/`**

A formal, machine-executable conformance test suite for AAIF runtimes:
- `tests/conformance/valid/` — 4 fixtures that MUST pass validation (Core, Tooled, Enterprise, Stateful checkpoint)
- `tests/conformance/invalid/` — 7 fixtures that MUST be rejected (missing name, missing goal, bad safety_level, bad routing_strategy, bad tool protocol, bad agent status, state missing agent_id)
- `tools/test_conformance.py` — test runner; exits 0 if all assertions pass. Usage: `python tools/test_conformance.py SC-006-agent-interchange-format`

**Reference implementation: `tools/aaif/`**

Python reference implementation of AAIF (SC-006):
- `tools/aaif/__init__.py` — `load(path)`, `loads(text)`, `validate(data)`, `info(data)`
- `tools/aaif/converters.py` — stub converters: `to_langgraph()`, `to_crewai()`, `to_autogen()`. Each returns `{config, unmapped, warnings}`.
- `tools/aaif/__main__.py` — CLI: `python -m tools.aaif validate <file>`, `info <file>`, `convert <file> --target langgraph|crewai|autogen`

**CBOR encoding specification: SPECIFICATION.md §T**

Documents how AAIF agent definitions may optionally be encoded as CBOR (RFC 8949) for bandwidth-constrained environments. No separate schema; round-trips through JSON for validation. Media type: `application/cbor; profile="https://github.com/Observalytics-SL/aaif/cbor"`.

**Platform Manifest discovery: SPECIFICATION.md §U**

Full specification for platform capability advertisement, publication convention (`.well-known/aaif-manifest.json`), and the 5-step capability negotiation workflow.

**New related standard: SC-013 Agent Registry Protocol (Proposed)**

`SC-013-agent-registry/README.md` introduces the proposed Agent Registry Protocol — the discovery, publishing, and trust layer for the AAIF ecosystem. Status: Proposed (schema and API not yet finalised; contributions welcome).

### Changed

- `context.jsonld` updated: added `platform`, `capabilities`, `conformance_level`, `intake_endpoint`, `vault_providers`, `manifest_url`, `aaif_versions_supported` terms
- README updated: file table, conformance levels table, What's new section

### Removed (none — full backward compatibility maintained)

---

## Remaining roadmap

### Future (unscheduled)

- SC-013 Agent Registry Protocol — advance from Proposed to Draft once a reference registry is deployed
- CBOR reference encoder/decoder (Python + TypeScript)
- Multi-language reference implementations (TypeScript, Go, Rust)
- W3C Community Group Note or IETF Internet-Draft submission

---



---

## [2.0.0] — 2026-06-10

### Added

**Root-level fields:**
- `agent_id` (string, uuid) — globally unique stable identifier; preserved on import/export
- `status` (enum: draft/active/deprecated) — lifecycle state
- `tags` (string[]) — labels for routing, search, and capability filtering

**agent.model:**
- `provider` (enum, 14 providers) — primary LLM provider identifier
- `fallbacks[]` — ordered fallback chain of `{provider, model, max_cost_usd_per_1k_tokens}`
- `routing_strategy` (enum) — `preferred_first` / `cost` / `latency` / `quality` / `round_robin`
- `params` — sampling parameters: `max_tokens`, `top_p`, `frequency_penalty`, `presence_penalty`, `stop`, `seed`
- `response_format` (enum) — `text` / `json` / `json_schema` / `markdown`

**agent.orchestration (new block):**
- `role` (enum) — `orchestrator` / `worker` / `evaluator` / `router` / `synthesizer`
- `subagents[]` — child agent references with `ref` (UUID/URI), `alias`, `role`, `when`, `pass_memory_keys`
- `handoff[]` — mid-run delegation rules with `condition`, `target_agent`, `pass_context`, `pass_memory`
- `pipeline[]` — ordered subagent aliases for sequential execution
- `parallel_execution` (boolean) — fan-out swarm mode
- `max_iterations` (integer) — agentic loop guard, default 10
- `consensus` — `{strategy, min_votes, referee_agent}` for resolving parallel output conflicts

**agent.context[].items:**
- `description` — why this context item is needed
- `refresh_ttl_seconds` — re-fetch interval for `url` type contexts

**agent.tools[].items:**
- `output_schema` — JSON Schema for tool responses
- `auth` — `{type, env_var, header, scopes, token_url}` for bearer/api_key/oauth2/aws_sigv4
- `cache_ttl_seconds` — response cache duration
- `timeout_seconds` — per-tool call timeout
- `rate_limit` — `{requests_per_minute, tokens_per_minute}`
- `name` now has pattern validation `^[a-zA-Z_][a-zA-Z0-9_-]{0,63}$`

**agent.memory[].items:**
- `backend` (enum, 8 options) — `in_memory` / `redis` / `postgres` / `sqlite` / `pinecone` / `weaviate` / `qdrant` / `chroma` / `custom`
- `ttl_seconds` — memory item expiry
- `embedding_model` — model for vector backends
- `retrieval_strategy` (enum) — `similarity` / `keyword` / `hybrid` / `recency`
- `top_k` — retrieved items per query

**agent.io:**
- `streaming` (boolean)
- `format` (enum) — `text` / `json` / `markdown` / `structured`
- `mode` (enum) — `sync` / `async` / `batch`

**agent.events (new block):**
- `triggers[]` — `{type, schedule, event_name, webhook_path, filter}` with types: `manual` / `schedule` / `webhook` / `message` / `event` / `agent_handoff` / `file_change`
- `on_start`, `on_complete`, `on_error`, `on_tool_call` — lifecycle hooks

**agent.runtime (new block):**
- `timeout_seconds`, `max_retries`, `retry_backoff`, `concurrency`, `streaming`, `async_execution`, `queue`, `environment`

**agent.telemetry (new block):**
- `tracing`, `log_level`, `metrics`, `trace_context_header`, `otlp_endpoint`

**agent.evaluation (new block):**
- `judge_model`, `metrics[]` (9 standard metric types with thresholds), `test_cases[]`

**agent.compliance (new block):**
- `safety_level`, `data_residency`, `pii_handling`, `audit_log`, `human_in_the_loop`

**agent:**
- `version` (semver) — agent definition version, independent of schema version
- `skills[]` — capability tags for routing and discovery

**provenance:**
- `updated_at` — last-modified timestamp
- `license` — SPDX license identifier
- `sc_refs[]` — dependencies on other Schema Commons standards

**examples:**
- `examples/orchestrator-pipeline.json` — sequential 4-agent BI pipeline orchestrator
- `examples/code-review-swarm.json` — parallel 3-reviewer swarm with consensus

**documentation:**
- `WHITEPAPER.md` — publication essay and standards readiness assessment
- `ABSTRACT.md` — structured abstract for registries, IETF I-D, and citation
- `ADOPTERS.md` — self-service adopter registry
- `CHANGELOG.md` — this file
- Enriched `context.jsonld` with full vocabulary mapping (schema.org, PROV-O, Dublin Core, AAIF vocab)

### Changed

- `sc_version` default updated from `"1.0.0"` to `"2.0.0"`
- `x-sc-version` in schema updated to `"2.0.0"`
- All existing examples updated to v2 with enriched fields

### Removed (none — full backward compatibility maintained)

All v1 fields remain valid. A v1 document continues to validate against the v2 schema.

---

## [1.0.0] — 2026-06-09

### Added

Initial public draft.

- `sc_standard`, `sc_version`
- `agent.name`, `agent.goal`, `agent.description`, `agent.instructions`
- `agent.model` — `preferred`, `min_context_tokens`, `temperature`
- `agent.context[]` — types: `text`, `file`, `url`, `dataset`, `schema_ref`
- `agent.tools[]` — `name`, `description`, `protocol` (function/mcp/http/openapi), `parameters_schema`, `endpoint`
- `agent.memory[]` — `scope` (user/session/task/long_term), `key`, `content`
- `agent.constraints[]`
- `agent.io` — `input_schema`, `output_schema`
- `provenance` — `authored_by`, `source_platform`, `created_at`, `signature`
- `context.jsonld` — basic vocabulary mapping
- `examples/invoice-chaser.json`, `examples/research-summarizer.json`

---

## Roadmap for v2.1 (planned)

- `auth.vault_ref` — reference to a secret in an external vault (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault)
- `agent.required_capabilities[]` — declare runtime capabilities the agent needs; enables capability negotiation on import
- `agent.model.params.extended` — additional provider-specific params pass-through object
- Formal runtime conformance test suite

## Roadmap for v3.0 (planned)

- `agent_state` — live state and checkpoint format for mid-run migration
- Streaming handoff wire format
- Agent registry protocol (candidate: new Schema Commons standard SC-0NN-agent-registry)
