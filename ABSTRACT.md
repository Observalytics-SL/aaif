# SC-006 AAIF — Abstract

**Standard:** SC-006 · **Full name:** Autonomous Agent Interchange Format
**Acronym:** AAIF · **Version:** 3.4.0 · **Status:** Public Draft
**License:** CC BY 4.0 · **Date:** June 2026
**Repository:** https://github.com/Observalytics-SL/Frameworks/tree/main/SC-006-agent-interchange-format
**Schema:** https://schemacommons.org/SC-006/agent.schema.json
**Namespace:** https://schemacommons.org/SC-006/vocab#

---

## One-paragraph abstract (for directories, registries, and citations)

The Autonomous Agent Interchange Format (AAIF, SC-006) is an open, vendor-neutral JSON Schema standard for the portable definition of AI agents. An AAIF document encapsulates an agent's identity, goal, system instructions, LLM provider preferences and fallback routing, multi-agent orchestration topology (sequential pipeline, parallel swarm, dynamic routing, mid-run handoff), tool catalogue (supporting function, MCP, HTTP, and OpenAPI protocols with structured authentication), memory configuration (including vector backends and retrieval strategies), runtime policy, OpenTelemetry telemetry settings, LLM-as-judge evaluation criteria, and compliance controls (data residency, PII handling, human-in-the-loop approval). An agent defined in AAIF can be validated offline, committed to version control, and imported into any conforming multi-agent LLM platform regardless of the original authoring environment. AAIF is part of Schema Commons, a family of open, CC BY 4.0 licensed data standards.

---

## Extended abstract (for conference submission, IETF I-D, or W3C Note)

### Problem

The multi-agent LLM platform ecosystem is fragmented across more than a dozen competing frameworks (LangGraph, CrewAI, AutoGen, Open WebUI, Cline, Semantic Kernel, and others), each with a proprietary agent definition format. This fragmentation prevents portability, complicates auditing, and forces organisations to re-implement agent logic when changing or combining platforms. Existing adjacent standards — the Model Context Protocol (MCP) for tool invocation and the A2A Agent Card for discovery — address specific sub-problems but do not provide a complete, portable agent definition.

### Contribution

AAIF defines a portable agent definition document as a JSON Schema (draft 2020-12) object with the following normative components:

1. **Identity** — globally unique `agent_id` (UUID), `status` lifecycle, semantic versioning.
2. **LLM routing** — primary provider and model, an ordered `fallbacks[]` chain spanning 16 enumerated providers plus a `custom` escape hatch (`provider_id` + `base_url`) for gateways like OpenRouter, Copilot, or self-hosted proxies, and a platform-level `routing_strategy` (preferred\_first, cost, latency, quality, round\_robin).
3. **Orchestration** — five agent roles (orchestrator, worker, evaluator, router, synthesizer), four topology patterns (sequential pipeline, parallel swarm, dynamic routing, mid-run handoff), loop guard (`max_iterations`), and a consensus mechanism (majority\_vote, best\_of\_n, referee, first\_success).
4. **Tools** — function, MCP, HTTP, and OpenAPI tool protocols with `parameters_schema`, `output_schema`, structured authentication (bearer, api\_key, OAuth2, AWS SigV4) via environment variable references, per-tool rate limits, and cache TTLs.
5. **Memory** — four scopes (user, session, task, long\_term) across eight storage backends, with vector retrieval configuration (embedding model, retrieval strategy, top\_k).
6. **Runtime** — timeout, retry backoff, concurrency, async/batch execution modes, named work queues.
7. **Telemetry** — OpenTelemetry tracing (with OTLP endpoint), Prometheus metrics, W3C Trace Context propagation.
8. **Evaluation** — LLM-as-judge model, nine standard metric types with threshold gates, golden test cases for CI/CD regression.
9. **Compliance** — four safety levels, data residency constraints (EU/US/UK/APAC), PII handling modes, audit log requirement, human-in-the-loop approval gates.
10. **Provenance** — author, source platform, timestamps, license, inter-standard references, optional Ed25519 signature.

AAIF v2.1 adds three backwards-compatible extensions: `auth.vault_ref` (structured reference to secrets in AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, GCP Secret Manager, or 1Password); `required_capabilities[]` (dot-namespaced vocabulary for capability negotiation, see §R); and `model.params.extended` (provider-specific pass-through parameters).

AAIF v3 introduces a companion schema, `agent-state.schema.json`, for portable agent state checkpoints. An Agent State document captures conversation history, memory snapshot (without embeddings), pipeline position, pending tool calls, and subagent states, enabling pause/resume, cross-platform live migration, and crash recovery. AAIF v3 also specifies a streaming handoff wire format (`application/x-aaif-handoff+ndjson`) for uninterrupted mid-generation platform migration.

All new fields in v2 are optional. The minimum conformant document requires only `sc_standard: "SC-006"`, `agent.name`, and `agent.goal`, preserving backward compatibility with v1.

### Design rationale

AAIF follows four design principles: *declare, don't bind* (model and tools are preferences, not hard requirements); *safety first-class* (constraints and compliance are normative, not advisory); *composable* (references to other Schema Commons standards are first-class context); *observable by default* (telemetry is opt-out, not opt-in).

### Relationship to adjacent standards

AAIF uses MCP as one of four tool protocols and is structurally compatible with A2A Agent Cards (an AAIF definition can generate a conformant Agent Card). AAIF does not replace either protocol; it sits above them as the agent's portable blueprint. AAIF's `agent-state.schema.json` (§Q) is also complementary to the IETF individual draft draft-gaikwad-aps-profile-00 (Agent Persistent State Profile, APS): APS specifies a storage-service class for hosting agent state, while AAIF specifies the portable document captured from a running agent — the former is the volume layer, the latter is the application-level checkpoint that could be stored on it. For telemetry, AAIF defers span-attribute semantics to the OpenTelemetry GenAI semantic conventions (or, as an acceptable alternative, OpenInference) rather than defining its own — see §N and §J of the specification.

### Validation

The schema is implemented as JSON Schema 2020-12. All four included examples validate against the schema. A Python reference validator is available in the Schema Commons tooling repository.

### Status and next steps

AAIF v3.4.0 is a Public Draft. The formal conformance test corpus and self-certification program (§Y), the platform capability manifest / discovery endpoint (§U), the extension registries (§X), and an OpenAI Assistants reference converter now ship. Priority gaps before a stable release: (1) reference-implementation converters for more runtimes (LangGraph, CrewAI, AutoGen); (2) SchemaStore registration; (3) external adopters beyond the reference runtime. Community contributions are invited.

---

## Keywords

AI agents · multi-agent systems · LLM orchestration · agent portability · interoperability · JSON Schema · Model Context Protocol · OpenTelemetry · compliance · Schema Commons

---

## Citation

```bibtex
@techreport{aaif-sc006-v3,
  title     = {Autonomous Agent Interchange Format (AAIF) — SC-006 v3.4.0},
  author    = {{Schema Commons Working Group}},
  year      = {2026},
  month     = {June},
  type      = {Public Draft},
  institution = {Schema Commons},
  url       = {https://schemacommons.org/SC-006/},
  note      = {CC BY 4.0. Schemas: agent.schema.json, agent-state.schema.json, platform-manifest.schema.json (all sc_version 3.4.0)}
}
```

---

## Contact

- **Issues and proposals:** https://github.com/Observalytics-SL/Frameworks/issues
- **Working group:** See CONTRIBUTING.md in the repository
- **General enquiries:** hello@schemacommons.org *(forthcoming)*
