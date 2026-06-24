# SC-006 · AAIF — Autonomous Agent Interchange Format — Specification

- **Standard:** SC-006 · **Acronym:** AAIF · **Version:** 3.4.0 (Draft) · **License:** CC BY 4.0

---

## Conventions & terminology

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in [BCP 14](https://www.rfc-editor.org/info/bcp14) ([RFC 2119](https://www.rfc-editor.org/rfc/rfc2119), [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174)) when, and only when, they appear in all capitals, as shown here.

| Term | Definition |
|------|------------|
| **AAIF document** | A JSON (or CBOR, §T) instance conforming to one of the three schemas: agent definition, Agent State, or platform manifest. |
| **Agent definition** | The primary document type (`agent.schema.json`): the portable declaration of one agent. |
| **Producer** | Software that emits AAIF documents (an exporter). |
| **Consumer / runtime** | Software that imports an AAIF document and executes or enforces it. |
| **Conformance level** | One of the cumulative levels in §M that a Producer or Consumer claims. |
| **Condition** | The structured-or-string routing/gating type defined in §V. |
| **Registry** | A community-maintained list of allowed identifiers for an open extension point (§X). |
| **Capability** | A dot-namespaced runtime feature string an agent may require and a platform may advertise (§R). |

This document is normative. Examples, tables marked *informative*, and the appendices on prior art (§N) are non-normative.

---

## A. Purpose & scope

AAIF defines a portable AI agent so a definition created in one runtime can be imported and executed in another. It standardizes the *declaration* of an agent — identity, goal, LLM preferences, tool catalogue, memory configuration, multi-agent topology, runtime policy, telemetry, evaluation, and compliance — not the execution loop itself.

**In scope:** name, goal, instructions, model preferences and fallbacks, provider routing, context (RAG sources), tools (function/MCP/HTTP/OpenAPI + auth), memory (scopes + backends), orchestration topology (orchestrator/worker/pipeline/swarm), runtime config, telemetry, evaluation, compliance, and provenance.

**Out of scope:** the execution loop, billing, streaming wire format, and provider-specific internal optimizations.

---

## B. Design principles

1. **Declare, don't bind** — model and tools are *preferences*; receivers MAY substitute equivalents.
2. **Provider-agnostic routing** — `model.fallbacks[]` and `model.routing_strategy` express intent across any LLM provider without hard-coding one.
3. **Tool-protocol agnostic** — supports `function`, `mcp`, `http`, `openapi` in a unified tool object.
4. **Safety is first-class** — `constraints[]` and `compliance` are normative; runtimes MUST enforce them.
5. **Composable** — `context[].schema_ref` can point at other Schema Commons standards; `orchestration.subagents[]` links to other AAIF definitions.
6. **Verifiable** — `provenance.signature` allows receivers to cryptographically verify an agent's origin.
7. **Observable by default** — `telemetry` and `evaluation` blocks are first-class, not afterthoughts.

---

## C. Object model

```
AgentDefinition (root)
├── agent_id          (UUID, assigned once)
├── status            (draft | active | deprecated)
├── tags[]
└── agent
    ├── name / version / description / goal / instructions / skills[]
    ├── model
    │   ├── provider / preferred
    │   ├── provider_id / base_url  ← custom/gateway providers (§F)
    │   ├── fallbacks[]         ← multi-provider routing
    │   ├── routing_strategy    ← cost | latency | quality | round_robin
    │   └── params / response_format
    ├── orchestration           ← multi-agent topology
    │   ├── role                (orchestrator | worker | evaluator | router | synthesizer)
    │   ├── subagents[]         ← child agent refs
    │   ├── handoff[]           ← mid-run delegation rules
    │   ├── pipeline[]          ← ordered sequential execution
    │   ├── parallel_execution  ← fan-out / swarm mode
    │   ├── max_iterations      ← loop guard
    │   └── consensus           ← majority_vote | best_of_n | referee
    ├── context[]               ← RAG sources (text/file/url/dataset/schema_ref)
    ├── tools[]                 ← function/mcp/http/openapi + auth + rate_limit
    ├── memory[]                ← scopes + backends (redis/vector/postgres/…)
    ├── constraints[]           ← hard guardrails (MUST honour)
    ├── io                      ← input/output schemas + streaming + mode
    ├── events                  ← triggers + lifecycle hooks
    ├── runtime                 ← timeout, retries, concurrency, queue
    ├── telemetry               ← OTEL tracing + metrics
    ├── evaluation              ← LLM-as-judge + test cases
    └── compliance              ← safety_level, data_residency, PII, audit
└── provenance                  ← author, platform, signature
```

---

## D. Field dictionary

### Root

| Field | Type | Req | Description |
|-------|------|-----|-------------|
| `sc_standard` | `"SC-006"` | ✓ | Standard identifier literal. |
| `sc_version` | string (semver) | | AAIF schema version. Default `"3.4.0"`. |
| `agent_id` | string (uuid) | | Stable UUID assigned at creation. Preserved on import/export. |
| `status` | enum | | `draft` / `active` / `deprecated`. |
| `tags` | string[] | | Labels for routing, search, filtering. |

### agent

| Field | Type | Req | Description |
|-------|------|-----|-------------|
| `agent.name` | string | ✓ | Human-readable name. |
| `agent.version` | string (semver) | | Agent definition version (independent of schema version). |
| `agent.description` | string | | What the agent does and for whom. |
| `agent.goal` | string | ✓ | Primary objective — defines success. |
| `agent.instructions` | string | | System prompt / persona / rules. Injected before every turn. |
| `agent.skills[]` | string[] | | Capability tags for routing (e.g. `"email"`, `"sql"`, `"code-review"`). |
| `agent.required_capabilities[]` | string[] | | Runtime capabilities this agent **requires**. An importing platform MUST reject or warn if any declared capability is unsupported. See §R for the standard vocabulary. |

### agent.model

| Field | Type | Description |
|-------|------|-------------|
| `provider` | enum | `openai` / `anthropic` / `google` / `vertex_ai` / `mistral` / `cohere` / `groq` / `ollama` / `azure_openai` / `bedrock` / `huggingface` / `together` / `fireworks` / `deepseek` / `xai` / `openrouter` / `custom`. Use `custom` for any provider/gateway not enumerated (GitHub Copilot, Cline-routed endpoints, self-hosted gateways) — see §F. |
| `provider_id` | string | **Required when `provider = "custom"`.** Stable identifier for the actual provider or gateway (e.g. `"copilot"`, `"openrouter"`, `"cline"`, `"litellm"`, `"vllm"`). Lets a runtime route deterministically without a dedicated enum value. |
| `base_url` | string (uri) | Optional API base URL for self-hosted or gateway providers (typically OpenAI-compatible). Used with `custom`, `ollama`, or `openrouter`. |
| `preferred` | string | Model ID in provider notation (e.g. `"gpt-4o"`, `"claude-opus-4-5"`). |
| `fallbacks[]` | array | Ordered `{provider, model, max_cost_usd_per_1k_tokens}` fallback chain. |
| `routing_strategy` | enum | `preferred_first` / `cost` / `latency` / `quality` / `round_robin`. |
| `min_context_tokens` | integer | Minimum required context window. Runtime MUST NOT route below this. |
| `temperature` | number 0–2 | Sampling temperature. |
| `params` | object | `max_tokens`, `top_p`, `frequency_penalty`, `presence_penalty`, `stop`, `seed`. |
| `params.extended` | object | **v2.1** — Provider-specific pass-through parameters not covered by the standard fields. The runtime forwards these verbatim to the provider API (e.g. `{"thinking": {"type": "enabled", "budget_tokens": 5000}}` for Anthropic extended thinking). `additionalProperties: true`. |
| `response_format` | enum | `text` / `json` / `json_schema` / `markdown`. |

### agent.orchestration

| Field | Type | Description |
|-------|------|-------------|
| `role` | enum | `orchestrator` / `worker` / `evaluator` / `router` / `synthesizer` |
| `subagents[]` | array | `{ref, alias, role, when, pass_memory_keys}` — child agents to invoke. `ref` is a UUID or URI. `when` is a **Condition** (§V). |
| `handoff[]` | array | `{condition, target_agent, pass_context, pass_memory}` — mid-run delegation. `condition` is a **Condition** (§V). |
| `pipeline[]` | string[] | Ordered list of subagent aliases for sequential pipelines. |
| `parallel_execution` | boolean | Fan-out: invoke all subagents simultaneously (swarm mode). |
| `max_iterations` | integer | Maximum agentic loop iterations. Loop guard. Default `10`. |
| `consensus` | object | `{strategy, min_votes, referee_agent}` — agreement mechanism for parallel outputs. |

### agent.context[]

| Field | Type | Description |
|-------|------|-------------|
| `type` | enum | `text` / `file` / `url` / `dataset` / `schema_ref` |
| `label` | string | Human label. |
| `value` | string | Inline text, path, URL, or schema URI. |
| `description` | string | Why this context is needed. |
| `refresh_ttl_seconds` | integer | Re-fetch interval for `url` type. 0 = once. |

### agent.tools[]

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Identifier used in function-call payloads (alphanumeric + `_`). |
| `description` | string | What the tool does. Used by the LLM for tool selection. |
| `protocol` | enum | `function` / `mcp` / `http` / `openapi` |
| `parameters_schema` | object | JSON Schema for inputs (OpenAI/Anthropic function-calling format). |
| `output_schema` | object | JSON Schema for the tool's response. |
| `endpoint` | string | URI / `mcp://<server>/<resource>`. |
| `auth` | object | `{type, env_var, vault_ref, header, scopes, token_url}`. Secret in env var or vault, never inline. |
| `auth.vault_ref` | object | **v2.1** — `{provider, path, key, version}`. Resolves the secret from an external vault (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, GCP Secret Manager, 1Password). Takes precedence over `env_var`. |
| `cache_ttl_seconds` | integer | Cache successful responses. 0 = no cache. |
| `timeout_seconds` | integer | Tool call timeout. |
| `rate_limit` | object | `{requests_per_minute, tokens_per_minute}`. |

### agent.memory[]

| Field | Type | Description |
|-------|------|-------------|
| `scope` | enum | `user` / `session` / `task` / `long_term` |
| `key` | string | Lookup key. |
| `content` | string | Memory content or vector store description. |
| `backend` | enum | `in_memory` / `redis` / `postgres` / `sqlite` / `pinecone` / `weaviate` / `qdrant` / `chroma` / `custom` |
| `ttl_seconds` | integer | Expiry. 0 = never. |
| `embedding_model` | string | For vector backends (e.g. `"text-embedding-3-small"`). |
| `retrieval_strategy` | enum | `similarity` / `keyword` / `hybrid` / `recency` |
| `top_k` | integer | Retrieved items per query. Default `5`. |

### agent.io

| Field | Type | Description |
|-------|------|-------------|
| `input_schema` | object | JSON Schema for the agent's input. |
| `output_schema` | object | JSON Schema for output. Used with `model.response_format = "json_schema"`. |
| `streaming` | boolean | Stream partial tokens. |
| `format` | enum | `text` / `json` / `markdown` / `structured` |
| `mode` | enum | `sync` / `async` / `batch` |

### agent.events

| Field | Type | Description |
|-------|------|-------------|
| `triggers[]` | array | `{type, schedule, event_name, webhook_path, filter}`. Types: `manual` / `schedule` / `webhook` / `message` / `event` / `agent_handoff` / `file_change`. `filter` is a **Condition** (§V). |
| `on_start` | string | Hook called on agent start. |
| `on_complete` | string | Hook called on success. |
| `on_error` | string | Hook called on failure. |
| `on_tool_call` | string | Middleware before every tool invocation (approval, logging). |

### agent.runtime

| Field | Type | Description |
|-------|------|-------------|
| `timeout_seconds` | integer | Max wall-clock time. Runtime MUST abort after this. |
| `max_retries` | integer | Auto-retry count on transient failure. Default `2`. |
| `retry_backoff` | enum | `fixed` / `linear` / `exponential`. Default `exponential`. |
| `concurrency` | integer | Max simultaneous instances. Default `1`. |
| `streaming` | boolean | Request streaming from the LLM provider. |
| `async_execution` | boolean | Return a job ID immediately; run in background. |
| `queue` | string | Named work queue for async execution. |
| `environment` | enum | `production` / `staging` / `development` / `test` |

### agent.telemetry

| Field | Type | Description |
|-------|------|-------------|
| `tracing` | boolean | Emit OpenTelemetry spans. Each agent run = root span. Default `true`. |
| `log_level` | enum | `debug` / `info` / `warn` / `error`. Default `info`. |
| `metrics` | boolean | Emit Prometheus-compatible metrics. Default `true`. |
| `trace_context_header` | string | W3C Trace Context header. Default `"traceparent"`. |
| `otlp_endpoint` | string | OTLP collector endpoint. Falls back to platform default if omitted. |

### agent.evaluation

| Field | Type | Description |
|-------|------|-------------|
| `judge_model` | string | LLM-as-judge model (should be ≥ quality of agent model). |
| `metrics[]` | array | `{name, threshold}`. Names: `faithfulness` / `relevance` / `coherence` / `toxicity` / `hallucination_rate` / `task_completion` / `latency_ms` / `cost_usd_per_run` / `tool_call_accuracy` / `custom` |
| `test_cases[]` | array | `{id, input, expected_output, criteria}` — golden set for regression. |

### agent.compliance

| Field | Type | Description |
|-------|------|-------------|
| `safety_level` | enum | `minimal` / `standard` / `strict` / `regulated` |
| `data_residency` | enum | `global` / `EU` / `US` / `UK` / `APAC` / `custom` |
| `pii_handling` | enum | `none` / `detect` / `anonymize` / `encrypt` / `reject` |
| `audit_log` | boolean | Require immutable audit trail. |
| `human_in_the_loop` | object | `{enabled, trigger, timeout_seconds}` — approval gate for irreversible actions. `trigger` is a **Condition** (§V). |

### provenance

| Field | Type | Description |
|-------|------|-------------|
| `authored_by` | string | Author (username, email, or DID). |
| `source_platform` | string | Origin platform (e.g. `"LangGraph"`, `"Open WebUI"`, `"CrewAI"`). |
| `created_at` | datetime | ISO 8601 UTC creation timestamp. |
| `updated_at` | datetime | ISO 8601 UTC last-modified timestamp. |
| `license` | string | SPDX ID or URL (e.g. `"CC-BY-4.0"`, `"MIT"`). |
| `sc_refs[]` | string[] | Other SC standards this agent depends on (e.g. `["SC-005"]`). |
| `signature` | string | Base64 Ed25519 signature over canonical JSON. |

---

## E. Multi-agent topology patterns

AAIF supports four topology patterns that cover the majority of multi-agent LLM architectures:

### 1. Sequential pipeline
Each agent's output is the next agent's input. Declare via `orchestration.pipeline[]`.

```
[Planner] → [Researcher] → [Writer] → [Reviewer]
```

Use when tasks have a clear sequential dependency order.

### 2. Parallel swarm (fan-out / fan-in)
An orchestrator fans out to multiple workers simultaneously, then a synthesizer merges results.
Set `orchestration.parallel_execution: true` and list workers in `subagents[]`.

```
              ┌─[Security Reviewer]──┐
[Orchestrator]─┤─[Style Reviewer]────┤─[Synthesizer]
              └─[Logic Reviewer]────┘
```

Use for independent parallel analysis (code review, multi-perspective research, ensemble scoring).

### 3. Dynamic routing
A `router` agent examines the input and dispatches to the appropriate specialist. Declare via `orchestration.role: "router"` and list candidates in `subagents[]` with `when` conditions.

```
[Router] ──when: "invoice task"──→ [Invoice Chaser]
         ──when: "research task"──→ [Research Summarizer]
         ──when: "code task"─────→ [Code Reviewer]
```

### 4. Handoff (mid-run delegation)
Any agent can hand off mid-run to another agent using `orchestration.handoff[]`. The receiving agent inherits context and optionally memory.

```
[Customer Support] ──→ [Billing Specialist]  (when: "billing query detected")
```

### Topology composition
These patterns compose. A pipeline step can itself be a swarm. A swarm worker can trigger a handoff. The `orchestration.role` field tells the executing runtime how to interpret the agent's orchestration config.

---

## F. LLM provider integration

A multi-agent platform integrating AAIF SHOULD implement provider routing as follows:

1. **Parse `model.provider` + `model.preferred`** as the primary route.
2. **If unavailable or rate-limited**, walk `model.fallbacks[]` in order.
3. **Apply `model.routing_strategy`** when multiple models are equally available:
   - `cost`: select cheapest model meeting `min_context_tokens`.
   - `latency`: select fastest based on observed p50 latency.
   - `quality`: select highest benchmark score (platform-defined ranking).
   - `round_robin`: distribute load evenly across available models.
   - `preferred_first`: always try declared order before optimization.
4. **Enforce `model.min_context_tokens`** — never route to a model with smaller window.
5. **Forward `model.params`** to the selected provider's API. Strip unsupported params gracefully.
6. **Enforce `model.response_format`** — for `json_schema`, pass `agent.io.output_schema` to the provider's structured output API.

### Supported provider IDs and example model IDs

| `provider` | Example `preferred` values |
|------------|---------------------------|
| `openai` | `gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini` |
| `anthropic` | `claude-opus-4-5`, `claude-sonnet-4-5`, `claude-haiku-3-5` |
| `google` | `gemini-2.5-pro`, `gemini-2.5-flash` |
| `mistral` | `mistral-large-latest`, `mistral-small-latest` |
| `groq` | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768` |
| `ollama` | `llama3.2`, `qwen2.5`, `phi4` |
| `azure_openai` | `gpt-4o` (deployment name) |
| `bedrock` | `amazon.nova-pro-v1:0`, `meta.llama3-70b-instruct-v1:0` |
| `deepseek` | `deepseek-chat`, `deepseek-reasoner` |
| `xai` | `grok-3`, `grok-3-mini` |
| `openrouter` | `anthropic/claude-opus-4-5`, `openai/gpt-4o`, `meta-llama/llama-3.3-70b` |
| `vertex_ai` | `gemini-2.5-pro`, `publishers/anthropic/models/claude-opus-4-5` |

### Providers outside the enum

The enum is a convenience list, not a closed set. For any provider, aggregator, or gateway not enumerated — **GitHub Copilot**, **Cline**-routed endpoints, **OpenRouter**-style gateways behind a custom URL, self-hosted **LiteLLM**/**vLLM** proxies — set:

```json
"model": {
  "provider": "custom",
  "provider_id": "copilot",
  "base_url": "https://api.githubcopilot.com",
  "preferred": "gpt-4o",
  "params": { "extended": { "...": "provider-specific params" } }
}
```

`provider_id` is **required** with `provider: "custom"` so a runtime can dispatch deterministically; `base_url` names the endpoint (usually OpenAI-compatible); `params.extended` carries any non-standard request fields verbatim. This keeps the standard open-ended without enum churn every time a new gateway appears.

---

## G. Tool protocol guide

### `function` — in-process callable
The tool is a function available in the agent's runtime. `parameters_schema` is forwarded as-is to the model's function-calling API (OpenAI, Anthropic, or Gemini tool_config format). No `endpoint` needed.

### `mcp` — Model Context Protocol
`endpoint` uses the form `mcp://<server-name>/<capability>` or a full WebSocket/stdio URI. The runtime connects to the MCP server and exposes its tools to the LLM. AAIF tool definitions act as a manifest; the MCP server provides the implementation.

### `http` — Raw REST
`endpoint` is the full URL. The runtime constructs a request using `parameters_schema` as the request body schema and `auth` for credentials. Use `output_schema` to parse the response.

### `openapi` — OpenAPI spec
`endpoint` points to an OpenAPI 3.x spec (URL or local path). The runtime parses the spec, exposes all or selected operations as tools, and handles auth via the spec's `securitySchemes` + `auth.env_var`.

---

## H. Memory backend guide

| Backend | Best for | Notes |
|---------|----------|-------|
| `in_memory` | Development, session memory | Lost on restart. No persistence. |
| `redis` | Fast key-value, TTL expiry | Good for `session` and `task` scopes. |
| `postgres` | Structured long-term memory | Good for `user` and `long_term` scopes. |
| `sqlite` | Local/offline agents | Single-file persistence. |
| `pinecone` | Cloud vector search | Requires `embedding_model`. |
| `weaviate` | Self-hosted vector + keyword | Hybrid search built-in. |
| `qdrant` | Self-hosted vector | Fast, open-source. |
| `chroma` | Embedded vector (dev/test) | Zero-infra for local agents. |

Set `retrieval_strategy: "hybrid"` with Weaviate or Qdrant for production RAG pipelines where both semantic similarity and keyword precision matter.

---

## I. Runtime & deployment

Runtimes consuming AAIF definitions MUST:
- Enforce `agent.constraints[]` by injecting them into the system prompt AND applying them as output filters.
- Abort execution after `runtime.timeout_seconds` and return an error.
- Respect `runtime.concurrency` — do not exceed this number of parallel instances.
- Propagate `telemetry.trace_context_header` across all agent-to-agent and agent-to-tool calls.
- Not persist `memory[scope=session]` items beyond the session boundary.
- Require human approval before any write tool call when `compliance.human_in_the_loop.enabled = true`.

Runtimes SHOULD:
- Honour `model.routing_strategy` when multiple models are available.
- Cache tool responses respecting `tools[].cache_ttl_seconds`.
- Emit OTEL traces to `telemetry.otlp_endpoint` if set.
- Run CI evaluation using `evaluation.test_cases[]` before promoting an agent to `status: "active"`.

---

## J. Telemetry & observability

Every conforming runtime SHOULD emit the following OpenTelemetry signals per agent run. For span attribute *semantics* specifically, runtimes SHOULD follow the **OpenTelemetry GenAI semantic conventions** (`gen_ai.*` attributes, `invoke_agent`/`chat`/`execute_tool` span tree) — the emerging convention already emitted or instrumented by LangChain, CrewAI, AutoGen, and AG2, and consumed by Datadog, Honeycomb, and New Relic. **OpenInference** (Arize) is an acceptable alternative convention covering the same ground with a ten-span-kind model (LLM, EMBEDDING, RETRIEVER, RERANKER, TOOL, CHAIN, AGENT, GUARDRAIL, EVALUATOR, PROMPT). AAIF does not mandate one over the other and does not define its own audit/event vocabulary as a third alternative — see the Related Work discussion in §N for why, and for the pointer to the separate, out-of-scope event-taxonomy discussion.

**Spans:**
- `aaif.agent.run` (root) — attributes: `agent.id`, `agent.name`, `agent.version`, `model.provider`, `model.name`
- `aaif.agent.tool_call` (child) — attributes: `tool.name`, `tool.protocol`, `tool.endpoint`
- `aaif.agent.llm_call` (child) — attributes: `llm.model`, `llm.provider`, `llm.input_tokens`, `llm.output_tokens`
- `aaif.agent.memory_read` / `aaif.agent.memory_write` — attributes: `memory.scope`, `memory.backend`
- `aaif.agent.handoff` — attributes: `target_agent.id`, `pass_context`

**Metrics:**
- `aaif_agent_run_duration_ms` (histogram)
- `aaif_agent_run_total` (counter, labels: `status=success|error|timeout`)
- `aaif_agent_llm_tokens_total` (counter, labels: `provider`, `model`, `type=input|output`)
- `aaif_agent_tool_calls_total` (counter, labels: `tool_name`, `status`)
- `aaif_agent_cost_usd_total` (counter, labels: `provider`, `model`)

---

## K. Evaluation & quality

### LLM-as-judge
Set `evaluation.judge_model` to a model ≥ quality of the agent model. The runtime runs each `test_cases[]` item, compares the agent output against `expected_output` using the `criteria` rubric, and produces a score. The run fails CI if any `metrics[].threshold` is not met.

### Recommended baseline thresholds

| Metric | Acceptable | Good | Excellent |
|--------|-----------|------|-----------|
| `faithfulness` | ≥ 0.75 | ≥ 0.85 | ≥ 0.95 |
| `relevance` | ≥ 0.70 | ≥ 0.80 | ≥ 0.90 |
| `task_completion` | ≥ 0.80 | ≥ 0.90 | ≥ 0.95 |
| `toxicity` | ≤ 0.05 | ≤ 0.02 | ≤ 0.01 |
| `hallucination_rate` | ≤ 0.15 | ≤ 0.07 | ≤ 0.02 |

---

## L. Security & compliance

- Receivers MUST treat imported `tools[].endpoint` as untrusted — apply capability gating before activation.
- Secrets MUST be stored in environment variables. The `auth.env_var` field names the variable; the value MUST NOT appear in the AAIF document.
- `constraints[]` MUST be enforced. Dropping a constraint is a conformance violation.
- Memory items may contain PII — runtimes MUST honour `scope` and apply `compliance.pii_handling`.
- Be alert to **prompt injection** in `context[type=url]` values fetched at runtime. Strip or sandbox untrusted content.
- `compliance.data_residency` MUST be respected — route only to providers with data centres in the declared region.
- `compliance.audit_log = true` requires an append-only, tamper-evident log of all invocations.
- `provenance.signature` should be verified before executing an agent from an untrusted source.

---

## M. Conformance levels

| Level | Requirements |
|-------|-------------|
| **Core** | Validates against schema; `agent.name` and `agent.goal` present. |
| **Tooled** | Core + ≥1 tool with `parameters_schema`. |
| **Portable** | Tooled + `constraints[]` non-empty + resolvable `tools[].endpoint`. |
| **Multi-agent** | Portable + `orchestration.role` declared + ≥1 `subagents[]` or `handoff[]`. |
| **Observable** | Portable + `telemetry.tracing = true` + ≥1 `evaluation.metrics[]`. |
| **Enterprise** | Observable + `compliance.safety_level` declared + `compliance.audit_log = true` + `provenance.signature` present. |
| **Stateful** *(advanced)* | Enterprise + `required_capabilities[]` declared + `state.checkpoint` capability + Agent State checkpoints (§Q) supported. |

### Conformance scope guidance

The levels are cumulative but **you do not need to climb to the top**. The bulk of AAIF's value — portable definitions, provider routing, tool/memory/orchestration interchange — is delivered at **Portable** through **Enterprise**. These levels are fully expressible in the static `agent.schema.json` and are the **recommended primary target** for a first implementation or reference runtime.

**Stateful** is a deliberately separate, *advanced* tier. It pulls in the v3 live-state surface — Agent State checkpoints (§Q), the cross-platform migration protocol, and the NDJSON streaming-handoff wire format (§S). That surface is large and stateful, with its own security obligations (signed migration tokens, checksums, session-scope isolation). A runtime SHOULD reach Enterprise conformance first and adopt Stateful only when live pause/resume or cross-runtime migration is an actual requirement. Claiming Enterprise conformance is meaningful on its own; Stateful is not a prerequisite for it.

---

## N. Related Work & Mapping to Prior Art

Before drafting this section, we looked specifically for an existing standard that does what AAIF does: define a portable, vendor-neutral *document* that an agent author writes once and any conforming runtime can import and execute. We did not find one. The frameworks in the table below (LangGraph, CrewAI, AutoGen, MemGPT, etc.) each have their own internal agent representation, and MCP and A2A each standardise an adjacent slice (tool invocation, agent discovery) — but none of them defines the full, importable agent record AAIF does. That absence is the gap AAIF fills, and it is worth stating plainly rather than either overselling AAIF as solving more than it does or inventing false modesty about competitors that do not exist.

Two adjacent efforts are close enough to the v3 Agent State surface (§Q) and the telemetry block (§J) that they deserve explicit acknowledgment, both to show real prior-art diligence and to draw a clear boundary so AAIF is not mistaken for either.

**draft-gaikwad-aps-profile-00** ("Agent Persistent State Profile", APS) is an active IETF individual draft addressing a real but different layer: a *storage service class* (an "AgentPersistentState" usage class with a versioned "PersistentStateLineOfService" schema) that lets a storage backend advertise itself to host agent state, with non-normative bindings to the SNIA Swordfish/Redfish storage-management standards, crash consistency, cryptographic erasure tied to identity, vector-index workloads, and Kubernetes/CSI integration. APS is about how a *volume* exposes itself as suitable for agent state; AAIF's `agent-state.schema.json` (§Q) is about what the *portable document* captured from a running agent looks like — conversation history, memory snapshot, pipeline position, pending tool calls, subagent states — for pause/resume/migration between runtimes. The two are complementary layers, not competing formats: an AAIF Agent State document is exactly the kind of payload that could be persisted on an APS-class volume. AAIF takes no position on, and does not depend on, the storage layer beneath a checkpoint.

For telemetry, AAIF's `agent.telemetry` block (§J) intentionally does not define its own span or event semantics. Two real, overlapping conventions already exist for this: the **OpenTelemetry GenAI semantic conventions** (`gen_ai.*` span attributes, an `invoke_agent` → `chat`/`execute_tool` span tree; experimental as of March 2026 but already emitted or instrumented by LangChain, CrewAI, AutoGen, AG2, and consumed natively by Datadog, Honeycomb, and New Relic), and **OpenInference** (Arize's OTel-based convention with ten span kinds: LLM, EMBEDDING, RETRIEVER, RERANKER, TOOL, CHAIN, AGENT, GUARDRAIL, EVALUATOR, PROMPT). AAIF defers to whichever of these the runtime already speaks rather than reinventing span semantics a third time — see §J. Separately, MCP's own published roadmap (modelcontextprotocol.io/development/roadmap, March 2026) lists "audit trails and observability" — end-to-end visibility into what a client requested and what a server did, in a form enterprises can feed into existing logging and compliance pipelines — as an acknowledged, currently unsolved "Enterprise Readiness" gap. That is honest evidence that the ecosystem has more than one unsolved fragmentation problem; it is evidence for the *existence* of fragmentation, not for AAIF's specific claim about portable agent definitions, and it should not be cited as if it were the latter.

Agent observability and audit-event vocabularies are deliberately **out of scope** for AAIF — it is not trying to be a third competing telemetry-semantics standard, and a separate, withdrawn effort to define one within this same project surfaced a direct naming collision with OWASP's own "Agent Observability Standard" work. See [`../external-contributions/owasp-aos-event-vocabulary/`](../external-contributions/owasp-aos-event-vocabulary/) for that fuller discussion. AAIF's `telemetry` block stays minimal by design: turn tracing on, point it at an endpoint, and let the runtime's existing OTel GenAI semconv or OpenInference instrumentation own the span shape.

| AAIF field | Maps to |
|------------|---------|
| `tools[].parameters_schema` | OpenAI / Anthropic / Gemini function-calling JSON Schema |
| `tools[].protocol = "mcp"` | Model Context Protocol (Anthropic, 2024) |
| `instructions` | System prompt / `AGENTS.md` / `CLAUDE.md` |
| `context[]` | RAG sources / attached files / knowledge base |
| `model.fallbacks[]` | LiteLLM router fallbacks / LangChain model fallbacks |
| `orchestration.pipeline[]` | LangGraph StateGraph edges / CrewAI task order |
| `orchestration.parallel_execution` | AutoGen `GroupChat` / CrewAI `Process.hierarchical` |
| `orchestration.role = "evaluator"` | LLM-as-judge / OpenAI Evals |
| `orchestration.consensus` | Mixture-of-Agents (MoA) / self-consistency sampling |
| `memory[scope=long_term]` | MemGPT archival memory / Mem0 persistent memory |
| `compliance.human_in_the_loop` | LangGraph `interrupt()` / HITL approval nodes |
| `telemetry.otlp_endpoint` | OpenTelemetry / LangSmith / Langfuse / Arize Phoenix |
| `provenance.signature` | W3C PROV / DIF VC (future) |
| `agent-state.schema.json` | draft-gaikwad-aps-profile-00 (storage layer, complementary — not a competing document format) |

---

## O. Versioning & changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06 | Initial public draft. |
| 2.0.0 | 2026-06 | Multi-agent orchestration topology; LLM provider routing with fallbacks; tool auth, rate limits, output schemas; memory backends; runtime config; telemetry (OTEL); LLM-as-judge evaluation; compliance block; enriched context.jsonld; four new examples (orchestrator pipeline + code review swarm). Backward-compatible: all new fields are optional. |
| 2.1.0 | 2026-06 | `auth.vault_ref` (AWS/HCP/Azure/GCP/1Password vault integration); `required_capabilities[]` (capability negotiation); `model.params.extended` (provider-specific pass-through). All backward-compatible. |
| 3.0.0 | 2026-06 | `agent-state.schema.json` — companion checkpoint schema for live state, pause/resume, cross-platform migration; streaming handoff wire format (§S). |
| 3.1.0 | 2026-06 | `platform-manifest.schema.json` — capability advertisement and negotiation (§U); CBOR binary encoding (§T). |
| 3.2.0 | 2026-06 | Structured **Condition** type (§V) for `when`/`handoff.condition`/`filter`/`hitl.trigger` — deterministic `jsonpath`/`jmespath`/`cel`/`jsonlogic`/`always`/`never` expressions, with bare strings demoted to advisory hints. Provider extensibility: `openrouter` + `vertex_ai` enum values, plus `model.provider_id` and `model.base_url` to make `provider: "custom"` deterministically routable. All backward-compatible (string conditions still validate). |
| 3.3.0 | 2026-06 | Reserved extension namespace (§W): `x-*` keys and `_comment` at document root of all three schemas. |
| 3.4.0 | 2026-06 | Community **extension registries** (§X) with IANA-style registration policies; **conformance self-certification** program (§Y) + `conformance-report.schema.json`; bidirectional OpenAI Assistants converter with round-trip proof; RFC 2119 terminology + §Z references. Backward-compatible. |

---

## P. FAQ

**Does this replace MCP?**
No — MCP is a tool invocation protocol. AAIF packages a complete agent definition and *references* MCP as one of four tool protocols.

**Does this replace LangGraph / CrewAI / AutoGen?**
No — those are execution runtimes. AAIF is the portable definition format. Think of it as the "agent Dockerfile" that any runtime can build from.

**Can two platforms exchange live running state?**
Yes, from v3. Export an Agent State document using `agent-state.schema.json`. It captures conversation history, memory snapshot, pipeline position, pending tool calls, and subagent states. The receiving platform imports the document and resumes execution. See §Q for the full protocol.

**How does provider routing work in practice?**
The executing platform implements a routing layer that reads `model.provider`, `model.preferred`, `model.fallbacks[]`, and `model.routing_strategy`. It selects a model, calls the appropriate provider SDK, and returns a unified response. LiteLLM is the reference implementation for this pattern.

**What happens when a constraint conflicts with a tool output?**
The runtime's constraint enforcement layer intercepts the output before it reaches the user and either rewrites it, redacts it, or raises an error, depending on `compliance.safety_level`.

**Are AAIF agent IDs stable?**
Yes. `agent_id` is assigned once at creation and MUST NOT change on import/export. Platforms should use it as the canonical deduplication key.

**What if the receiving platform does not support a required capability?**
The platform MUST either refuse to import the agent with a descriptive error listing the unsupported capabilities, or import with a prominent warning and disable the dependent features. Silent capability stripping is a conformance violation.

**How do vault secrets work?**
Declare `auth.vault_ref` with the vault provider, path, and optional key. The runtime resolves the secret at execution time using its own configured vault credentials. The secret value MUST NOT appear in the AAIF document. Both `env_var` and `vault_ref` may be declared; `vault_ref` takes precedence.

---

## Q. Agent State & Checkpointing

AAIF v3 introduces a companion schema — `agent-state.schema.json` — for capturing, serialising, and restoring the complete execution state of a running agent. This enables three use cases:

1. **Pause and resume** — an operator pauses a running agent (e.g. for inspection or rate-limit cooldown), captures a checkpoint, and resumes it later on the same or a different platform.
2. **Cross-platform live migration** — an agent running on LangGraph is exported mid-run and imported into CrewAI, which resumes execution at the exact pipeline step where the agent was paused.
3. **Crash recovery** — if the runtime crashes, the last checkpoint is used to restart the agent without replaying the full conversation.

### Agent State document structure

| Field | Type | Description |
|-------|------|-------------|
| `state_id` | uuid | ✓ Unique checkpoint ID. New UUID per checkpoint, even for the same run. |
| `agent_id` | uuid | ✓ Links to the agent definition (agent.schema.json). |
| `run_id` | uuid | Groups all checkpoints for one execution run. |
| `agent_version` | string | Agent definition version at capture time. |
| `checkpoint_at` | datetime | ✓ UTC timestamp of capture. |
| `status` | enum | ✓ `running` / `paused` / `awaiting_approval` / `awaiting_tool_result` / `completed` / `failed` / `migrating` |
| `iteration` | integer | Current agentic loop count. Runtime enforces `max_iterations` on restore. |
| `pipeline_position` | object | `{current_step, completed_steps[], remaining_steps[], current_subagent, parallel_slot}` |
| `conversation[]` | array | Full message history. Each item: `{role, content, tool_call_id, tool_name, token_count, timestamp}`. On restore, truncate from the oldest end if the model context window is smaller. |
| `memory_snapshot[]` | array | All in-scope memory items: `{scope, key, content, backend, captured_at, ttl_remaining_seconds}`. Vector embeddings are NOT serialised — re-computed on restore. |
| `pending_tool_calls[]` | array | In-flight or queued tool calls: `{id, tool_name, arguments, status, submitted_at, callback_url}`. |
| `subagent_states[]` | array | Per-subagent summaries: `{alias, agent_id, state_id, status, output}`. For deep migration, each active subagent exports its own Agent State document. |
| `variables` | object | Named task-scope variables (free-form key-value). |
| `approval_request` | object | Present when `status = "awaiting_approval"`. Contains `{trigger_description, pending_action, requested_at, timeout_at, approver_hint}`. |
| `error` | object | Present when `status = "failed"`. Contains `{code, message, step, occurred_at, retries_remaining, stack_trace}`. |
| `provenance` | object | `{source_platform, source_runtime_version, captured_by, target_platform, migration_token, checksum}`. `checksum` is a SHA-256 hex digest of the canonical JSON (excluding the checksum field itself). The receiving platform MUST verify it before restoring. |

### Migration protocol

A cross-platform migration follows these steps:

```
1. Source platform captures Agent State (status = "paused" or "migrating")
2. Source platform issues a short-lived migration_token (signed, expiry ≤ 15 minutes)
3. Agent State document is transferred to the receiving platform (out-of-band: API, file, message queue)
4. Receiving platform verifies: checksum, migration_token, and that agent_id matches a known agent definition
5. Receiving platform imports the state: loads memory, restores conversation, resumes at pipeline_position.current_step
6. Receiving platform re-issues any pending_tool_calls that are still in-flight (or marks them timed-out)
7. Execution resumes
```

### Security requirements for Agent State

- The `migration_token` MUST be a signed, short-lived token. The receiving platform MUST verify the signature before accepting state.
- The `checksum` MUST be verified before restoring. A checksum mismatch indicates tampering or corruption.
- Memory items with `scope = "session"` MUST NOT be restored into a different user's session.
- The `stack_trace` field SHOULD be stripped before exporting a checkpoint from the originating platform.
- Agent State documents contain conversation history and memory, which may include PII. Apply the same `compliance.pii_handling` policy that governs the agent definition.

---

## R. Capability Negotiation

The `agent.required_capabilities[]` field (v2.1) declares what the agent needs from its executing runtime. A platform MUST check all declared capabilities before accepting an agent definition.

### Standard capability vocabulary

Capabilities use a dot-namespaced string format: `<category>.<capability>`.

| Capability string | Category | Meaning |
|-------------------|----------|---------|
| `tool.function` | Tool | In-process function calling |
| `tool.mcp` | Tool | Model Context Protocol tool invocation |
| `tool.http` | Tool | Raw HTTP tool calls |
| `tool.openapi` | Tool | OpenAPI spec parsing and invocation |
| `memory.vector` | Memory | Any vector storage backend |
| `memory.redis` | Memory | Redis backend specifically |
| `memory.postgres` | Memory | PostgreSQL backend specifically |
| `memory.pinecone` | Memory | Pinecone vector backend |
| `memory.qdrant` | Memory | Qdrant vector backend |
| `orchestration.parallel` | Orchestration | Parallel subagent fan-out |
| `orchestration.handoff` | Orchestration | Mid-run handoff between agents |
| `orchestration.pipeline` | Orchestration | Sequential pipeline execution |
| `orchestration.consensus` | Orchestration | Consensus/voting mechanisms |
| `telemetry.otel` | Observability | OpenTelemetry tracing |
| `compliance.data_residency` | Compliance | Enforced data residency routing |
| `compliance.hitl` | Compliance | Human-in-the-loop approval gates |
| `compliance.audit_log` | Compliance | Immutable audit logging |
| `io.streaming` | IO | Streaming token output |
| `io.async` | IO | Async execution with job ID |
| `io.batch` | IO | Batch input mode |
| `auth.vault` | Security | External vault secret resolution (`vault_ref`) |
| `state.checkpoint` | State | Agent State checkpoint capture (v3) |
| `state.restore` | State | Agent State restore and resume (v3) |

### Platform behaviour on unsatisfied capabilities

| Safety level | Behaviour when a required capability is unsatisfied |
|--------------|-----------------------------------------------------|
| `minimal` | Log a warning and continue (capability is silently skipped). |
| `standard` | Import the agent but disable the feature; surface a warning in the operator UI. |
| `strict` | Reject the import with a descriptive error listing unsatisfied capabilities. |
| `regulated` | Reject the import. Failure is audit-logged. |

Platforms SHOULD publish a machine-readable list of the capabilities they support, using the same vocabulary, so agents can be matched to compatible platforms automatically.

---

## S. Streaming Handoff Wire Format

AAIF v3 defines a wire format for streaming state transfer during live handoffs. This is used when an agent must be handed off mid-generation — e.g. when a streaming response must continue without interruption on a new platform.

### Media type

```
Content-Type: application/x-aaif-handoff+ndjson
```

Each line is a newline-delimited JSON (NDJSON) object with a `type` discriminator field.

### Message types

| `type` | Purpose | Required fields |
|--------|---------|-----------------|
| `handoff_init` | Opens the stream; declares metadata. | `state_id`, `agent_id`, `run_id`, `source_platform`, `migration_token` |
| `context_chunk` | Sends a slice of the conversation history. | `index`, `messages[]` (array of conversation items) |
| `memory_item` | Sends one memory item. | `scope`, `key`, `content` |
| `pipeline_state` | Sends pipeline position and variables. | `pipeline_position`, `variables`, `iteration` |
| `pending_tool` | Sends one pending tool call. | `id`, `tool_name`, `arguments`, `status` |
| `subagent_ref` | References an active subagent's state. | `alias`, `agent_id`, `state_id` |
| `handoff_complete` | Closes the stream successfully. | `checksum` (SHA-256 of the full reconstructed Agent State) |
| `handoff_error` | Terminates the stream with an error. | `code`, `message` |

### Example stream

```ndjson
{"type":"handoff_init","state_id":"d7e8...","agent_id":"a1b2...","run_id":"e8f9...","source_platform":"LangGraph","migration_token":"eyJhbGci..."}
{"type":"context_chunk","index":0,"messages":[{"role":"system","content":"You are..."},{"role":"user","content":"..."}]}
{"type":"context_chunk","index":1,"messages":[{"role":"assistant","content":"..."},{"role":"tool","content":"...","tool_call_id":"call_abc"}]}
{"type":"memory_item","scope":"user","key":"company_name","content":"Rivera Consulting"}
{"type":"pipeline_state","pipeline_position":{"current_step":"send_reminders","completed_steps":["list_overdue_invoices"]},"variables":{"invoices_count":"3"},"iteration":3}
{"type":"handoff_complete","checksum":"a3f7c21e..."}
```

### Security requirements

- The receiving platform MUST verify the `migration_token` before processing any subsequent messages.
- If a `handoff_error` message is received, the receiving platform MUST discard all accumulated state and NOT resume execution.
- The stream MUST be transmitted over TLS (HTTPS/WSS). Plaintext streaming handoffs are non-conformant.
- The `checksum` in `handoff_complete` MUST be verified against the reconstructed Agent State before execution is resumed.


## T. Binary Encoding (CBOR)

AAIF documents are canonically JSON. For bandwidth-constrained transports — embedded runtimes, IoT-adjacent edge deployments, high-throughput agent mesh bus — implementations MAY encode AAIF documents as **CBOR** (Concise Binary Object Representation, [RFC 8949](https://www.rfc-editor.org/rfc/rfc8949)).

### Rules

1. **Logical structure is identical.** Field names, enum values, required/optional semantics, and all constraints in `agent.schema.json` and `agent-state.schema.json` apply without modification to CBOR-encoded documents.
2. **No separate schema.** There is no `agent.cbor-schema`; validators round-trip to JSON before schema validation.
3. **Media type.** CBOR-encoded AAIF documents use the media type `application/cbor` with a content-type parameter: `application/cbor; profile="https://schemacommons.org/SC-006/cbor"`.
4. **Diagnostic notation.** When displaying or logging a CBOR-encoded AAIF document, use CBOR diagnostic notation (RFC 8949 §8) — human-readable but lossless.
5. **Integer key maps.** Implementations MUST NOT use integer keys (CBOR Major Type 0 map) as a compression scheme. Field names remain UTF-8 text strings so that JSON round-trips are lossless.
6. **Interop requirement.** Any platform claiming AAIF conformance at **Portable** level or above that accepts CBOR-encoded agent definitions MUST also accept the equivalent JSON encoding and produce identical behaviour.

### Reference

A conformance-tested Python converter is available via the `aaif` reference implementation:

```python
import cbor2, json
from aaif import validate

# JSON → CBOR
with open("invoice-chaser.json") as f:
    data = json.load(f)
errors = validate(data)
if not errors:
    cbor_bytes = cbor2.dumps(data)

# CBOR → JSON (round-trip)
decoded = cbor2.loads(cbor_bytes)
assert decoded == data
```

---

## U. Platform Manifest and Capability Advertisement

A platform that accepts AAIF agent definitions SHOULD publish a **Platform Manifest** — a machine-readable document describing the platform's capabilities. The manifest allows orchestrators, CI/CD pipelines, and agent management systems to perform capability negotiation _before_ dispatching an agent to a runtime.

### Schema

Platform manifests validate against `schema/platform-manifest.schema.json` (introduced in v3.1). The manifest is a JSON document with `sc_standard: "SC-006"` and a `platform` block covering:

| Section | Key fields |
|---------|-----------|
| Identity | `name`, `version`, `vendor`, `manifest_url` |
| Conformance | `aaif_conformance_level`, `aaif_versions_supported` |
| Tool capabilities | `capabilities.tool.*` — supported protocols and parallel calls |
| Memory capabilities | `capabilities.memory.*` — which backends are available |
| Model capabilities | `capabilities.model.providers[]`, `routing_strategies[]` |
| Orchestration | `capabilities.orchestration.*` — topologies, `max_subagents`, and `condition_languages[]` (which Condition langs from §V the platform evaluates) |
| Auth / Vault | `capabilities.auth.vault.providers[]` — which vault providers the platform resolves |
| State | `capabilities.state.checkpoint`, `live_migration`, `streaming_handoff` |
| Compliance | `capabilities.compliance.data_residency_regions[]`, PII/HITL/audit support |
| Intake endpoint | `platform.intake_endpoint` — URL to POST an AAIF definition for import |

### Publication convention

Platforms SHOULD publish the manifest at a well-known URL path: `/.well-known/aaif-manifest.json`. Alternatively, the manifest URL may be advertised in API documentation.

### Capability negotiation workflow

1. Orchestrator fetches the target platform's manifest.
2. For each entry in `agent.required_capabilities[]`, the orchestrator checks whether the capability is present and `true` in the manifest's `capabilities` block.
3. Vault capabilities are checked as: `agent.tools[*].auth.vault_ref.provider` ∈ `manifest.platform.capabilities.auth.vault.providers[]`.
4. If all required capabilities are satisfied: dispatch the agent.
5. If one or more capabilities are unsatisfied: consult `agent.compliance.safety_level`:
   - `minimal` / `standard` → log a warning, dispatch with degraded functionality.
   - `strict` / `regulated` → abort dispatch; return a structured error to the caller.

### Example

See `examples/platform-manifest.json` for a full example manifest at `Stateful` conformance level.

---

## V. Condition Expressions (routing & gating)

Several fields decide *whether* or *when* something runs: `orchestration.subagents[].when`, `orchestration.handoff[].condition`, `events.triggers[].filter`, and `compliance.human_in_the_loop.trigger`. Each accepts the shared **Condition** type, which has two forms.

### Two forms — prefer the structured one

**1. Structured (RECOMMENDED — deterministic, portable).** An object naming an expression language and an expression:

```json
{ "lang": "jsonpath", "expr": "$.task.type", "nl": "task type is code_review" }
```

| `lang` | `expr` shape | Evaluation |
|--------|--------------|-----------|
| `jsonpath` | string | Evaluate the JSONPath query against the input/payload; truthy if it yields a non-empty result. |
| `jmespath` | string | Evaluate the JMESPath query; truthy if the result is truthy. |
| `cel` | string | [Common Expression Language](https://github.com/google/cel-spec) boolean expression. |
| `jsonlogic` | object | A [JsonLogic](https://jsonlogic.com) rule evaluated against the payload. |
| `always` | *(omitted)* | Constant `true`. |
| `never` | *(omitted)* | Constant `false`. |

`expr` is REQUIRED for `jsonpath`/`jmespath`/`cel`/`jsonlogic` and MUST be omitted (or ignored) for `always`/`never`. The optional `nl` field is a human-readable description for logs and UIs — it is advisory; the structured `expr` is authoritative.

**2. String (natural-language hint — non-deterministic).** A bare string is accepted for authoring convenience and backward compatibility:

```json
"when": "after all three reviewers complete"
```

A string condition is a **hint only**. Different runtimes interpret it differently (or via an LLM), so it MUST NOT be relied on for portable, reproducible routing. Runtimes SHOULD emit a portability warning when they route on a string condition.

### Normative rules

- A runtime that supports a declared `lang` MUST evaluate the structured form deterministically and MUST NOT fall back to an LLM interpretation of `nl`.
- A runtime that does **not** support a declared `lang` MUST treat the condition as unsatisfiable-unknown and apply the same behaviour as an unsatisfied `required_capabilities` entry per the agent's `compliance.safety_level` (§R): `minimal`/`standard` MAY degrade with a warning; `strict`/`regulated` MUST reject the agent.
- Authors targeting **Portable** conformance or above SHOULD use the structured form for every condition that affects control flow. The string form is acceptable for `always`-style or purely advisory cases.
- `orchestration.consensus.referee_agent` is **not** a condition — it is a structured agent reference (ID or alias), already deterministic.

### Recommended `lang` support

A conforming runtime SHOULD support at least `always`, `never`, and one of `jsonpath`/`jmespath`/`cel`. Platforms SHOULD advertise supported condition languages in their Platform Manifest (§U).

---

## W. Extension keys & forward compatibility

AAIF documents are validated strictly: every object uses `additionalProperties: false`, so an unrecognised key is a validation error. This catches typos and silent data loss. But strictness without an escape hatch blocks tools from attaching their own metadata and makes forward-compatibility brittle. AAIF therefore reserves an **extension namespace** at the document root of all three schemas (`agent`, `agent-state`, `platform-manifest`).

### Reserved keys

- **`x-*`** — any property whose name begins with `x-` is an **extension key**. It carries vendor-, tool-, or platform-specific metadata. Extension values are opaque to the standard.
- **`_comment`** — a non-normative, human-readable annotation (string). Equivalent to a code comment; ignored by runtimes.

These are permitted at the **document root**. Finer-grained vendor data SHOULD instead use the existing typed mechanisms: `tags[]` and `skills[]` for labels, and `model.params.extended` for provider-specific sampling parameters.

### Normative rules

- A conforming runtime **MUST ignore** any extension key it does not understand, and **MUST NOT** let an unknown `x-*` key change agent behaviour, routing, or safety decisions.
- A runtime **MUST NOT** reject a document solely because it carries `x-*` or `_comment` keys.
- Extension keys **MUST NOT** be used to smuggle behaviour that a future MINOR version might standardise under a normative name; when a concept is standardised, authors SHOULD migrate off the `x-` key.
- Tooling that re-serialises a document SHOULD round-trip unknown `x-*` keys unchanged (preserve-on-passthrough) so that metadata is not lost in transit.

### Validator metadata

`x-sc-schema` is a validator hint that names the target schema file for a multi-schema conformance harness (e.g. `"agent.schema.json"`). It lives in the `x-` namespace and is therefore valid in any document, but it is **harness metadata, not agent data** — conformance tooling MAY strip it (and `_comment`) before validating. Because the extension namespace makes both keys schema-legal, stripping is an optimisation, not a correctness requirement: a conformance fixture with a real rule violation now rejects for that violation whether or not annotation keys were stripped first.

---

## X. Extension Registries & Registration Policy

AAIF has a handful of **open extension points** — places where the ecosystem keeps inventing new values: LLM providers, runtime capabilities, condition languages, vault providers, memory backends, tool protocols. If every new value required a new schema version, the standard would either ossify or fragment into vendor forks. AAIF instead borrows the mechanism that has kept IANA's IP, MIME, and HTTP registries stable and open for decades: the normative schema enumerates a *recommended* set, and a **community registry** holds the authoritative living list.

### The registries

Each registry is a machine-readable JSON file under [`registries/`](registries/), validated against [`registries/registry.schema.json`](registries/registry.schema.json):

| Registry | Extension point | Policy |
|----------|-----------------|--------|
| `providers.json` | `model.provider` | Specification Required |
| `capabilities.json` | `required_capabilities[]`, manifest capabilities | Expert Review |
| `condition-languages.json` | Condition `lang` (§V) | Specification Required |
| `vault-providers.json` | `auth.vault_ref.provider` | Specification Required |
| `memory-backends.json` | `memory[].backend` | Specification Required |
| `tool-protocols.json` | `tools[].protocol` | Standards Action |

### Relationship between the schema enum and the registry (normative)

- The `enum` in `agent.schema.json` for each extension point is a **convenience subset**, not a closed world. It MUST be a subset of the `status: "standard"` entries in the corresponding registry. `tools/test_registries.py` enforces this in CI.
- A value that is registered as `standard` but not yet in the schema `enum` is **conformant**. Runtimes SHOULD accept it. (The enum is widened to match the registry on the next MINOR release; the registry is authoritative in the interim.)
- A value that is in neither the enum nor the registry MUST be carried through the documented escape hatch — `model.provider: "custom"` + `model.provider_id` for providers, or an `x-` extension key (§W) for other metadata — never by inventing an unregistered bare enum value.

### Identifier status

`standard` (ratified, rely on it) · `provisional` (usable, may change — prefer the `custom` escape hatch until promoted) · `deprecated` (back-compat only) · `reserved` (name held, not yet usable).

### Registration policies

| Policy | Requirement to add an entry |
|--------|-----------------------------|
| **First Come First Served** | Unique id + one-line description. |
| **Specification Required** | The above + a stable public spec/API/docs URL. |
| **Expert Review** | The above + a standard Editor's sign-off that the entry is orthogonal and well-scoped. |
| **Standards Action** | A normative schema change shipped in a new MINOR version (every runtime must implement it). |

### How to register

Open a PR adding an entry to the relevant file (see [`registries/README.md`](registries/README.md)), default `status: "provisional"`, run `python tools/test_registries.py`, title it `SC-006: register <registry> id '<id>'`. Lazy consensus applies (§GOVERNANCE): no Editor objection within 14 days = accepted. **No registration is needed to experiment** — `custom`/`provider_id` and `x-` keys are always valid.

### IANA-style considerations (for formal publication)

This section IS the "IANA Considerations" of AAIF. A future IETF Internet-Draft or W3C submission would point an external registry operator at these files. Until then the registries are operated by the Schema Commons Steering Council under the policies above.

---

## Y. Conformance & Self-Certification

Conformance is **per level** (§M) and is **self-certified**: there is no central certifying authority, mirroring how a project claims "valid HTML5" or "OCI-compliant." Credibility comes from the claim being *machine-checkable against a public test suite*, not from a gatekeeper.

### What a conformance claim means

A platform claims a level L for a direction (`producer`, `consumer`, or `both`):

- **Producer** at level L: every AAIF document the platform **exports** validates against `agent.schema.json` and satisfies the level-L predicates in §M.
- **Consumer** at level L: the platform **imports and honours** every construct required at level L — including the normative MUSTs for that level (e.g. a Consumer at *Portable* enforces `constraints[]`; at *Enterprise* it enforces `compliance` and audit logging; unsupported `required_capabilities[]` are handled per the agent's `safety_level`, §R).

### The public test suite

The normative test corpus is [`tests/conformance/`](tests/conformance/): every file in `valid/` MUST validate, every file in `invalid/` MUST be rejected. Run it with:

```bash
python tools/test_conformance.py SC-006-agent-interchange-format
```

A platform SHOULD additionally pass round-trip interoperability for any framework it converts to/from (see `tools/test_roundtrip.py`).

### Self-certification report

A platform publishes a **Conformance Report** validating against [`schema/conformance-report.schema.json`](schema/conformance-report.schema.json), at the well-known path `/.well-known/aaif-conformance.json`. The report states the claimed level, direction, AAIF versions, test-suite result, and supported registries/capabilities. Orchestrators and the [ADOPTERS.md](ADOPTERS.md) registry consume it. See `examples/conformance-report.json` and [CONFORMANCE.md](CONFORMANCE.md) for the full process.

---

## Z. References

### Normative references

- **[RFC 2119]** Bradner, S., "Key words for use in RFCs to Indicate Requirement Levels", BCP 14, RFC 2119, 1997.
- **[RFC 8174]** Leiba, B., "Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words", BCP 14, RFC 8174, 2017.
- **[RFC 8259]** Bray, T., Ed., "The JavaScript Object Notation (JSON) Data Interchange Format", STD 90, RFC 8259, 2017.
- **[RFC 8949]** Bormann, C. and P. Hoffman, "Concise Binary Object Representation (CBOR)", STD 94, RFC 8949, 2020.
- **[JSON-SCHEMA]** Wright, A., et al., "JSON Schema: A Media Type for Describing JSON Documents", Draft 2020-12.
- **[RFC 9535]** Gössner, S., et al., "JSONPath: Query Expressions for JSON", RFC 9535, 2024.
- **[CEL]** Google, "Common Expression Language Specification", https://github.com/google/cel-spec.

### Informative references

- **[MCP]** Anthropic, "Model Context Protocol", 2024, https://modelcontextprotocol.io.
- **[MCP-ROADMAP]** Model Context Protocol, "Roadmap", 2026-03-05, https://modelcontextprotocol.io/development/roadmap.
- **[OTEL]** OpenTelemetry, "OpenTelemetry Specification", https://opentelemetry.io/docs/specs/.
- **[OTEL-GENAI]** OpenTelemetry, "Semantic Conventions for Generative AI systems", experimental, https://opentelemetry.io/docs/specs/semconv/gen-ai/.
- **[OPENINFERENCE]** Arize AI, "OpenInference Semantic Conventions", https://github.com/Arize-ai/openinference.
- **[APS]** Gaikwad, et al., "Agent Persistent State Profile (APS)", Internet-Draft, draft-gaikwad-aps-profile-00 (work in progress), IETF.
- **[PROV-O]** W3C, "PROV-O: The PROV Ontology", W3C Recommendation, 2013.
- **[JMESPath]** "JMESPath Specification", https://jmespath.org/specification.html.
- **[JsonLogic]** "JsonLogic", https://jsonlogic.com.
- **[W3C-TRACE]** W3C, "Trace Context", W3C Recommendation, 2021.
- **[SPDX]** Linux Foundation, "SPDX License List", https://spdx.org/licenses/.

### Author / editor

Edited under the Schema Commons governance model ([GOVERNANCE.md](../GOVERNANCE.md)). Contributions are licensed CC BY 4.0 (specification) and Apache 2.0 (tooling). To cite, see [CITATION.cff](CITATION.cff).

---
