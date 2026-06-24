# Autonomous Agent Interchange Format (AAIF): A Vendor-Neutral Open Standard for Portable AI Agent Definitions

**Bob van Bussel**
Observalytics SL · bob@observalytics.com
Schema Commons Working Group
June 2026

---

> **Abstract**
>
> The multi-agent LLM platform ecosystem is fragmented across more than a dozen incompatible frameworks — LangGraph, CrewAI, AutoGen, Open WebUI, and others — each encoding agent definitions in a proprietary format. An agent's goal, instructions, model preferences, tool catalogue, memory configuration, and compliance constraints are conceptually identical across platforms but syntactically incompatible, making agents impossible to migrate without manual reconstruction. This portability gap is not merely a developer inconvenience: agent definitions encode compliance obligations — data residency constraints, PII handling policies, human-in-the-loop approval gates — and a proprietary format is therefore an audit and governance gap, not only a technical one. The Autonomous Agent Interchange Format (AAIF, Schema Commons SC-006) addresses this gap through a JSON Schema 2020-12 document format published as an open standard under CC BY 4.0. An AAIF document carries ten normative components: stable agent identity (UUID, SemVer versioning, lifecycle states), LLM provider routing and fallback chains across 16 enumerated providers plus a custom escape hatch, multi-agent orchestration topology (five roles, four patterns), a tool catalogue supporting function, MCP, HTTP, and OpenAPI protocols with structured authentication and vault-reference secrets management, memory configuration across four scopes and eight backends, runtime policy, OpenTelemetry telemetry, LLM-as-judge evaluation with CI/CD-gateable test cases, and compliance controls. A companion schema, `agent-state.schema.json`, enables live migration of running agents across platforms via a 7-step checkpoint protocol and an NDJSON streaming handoff wire format. The standard ships with four reference examples, a Python validator and converter toolchain, a bidirectional OpenAI Assistants converter with round-trip proof, a conformance test corpus, and a self-certification programme. An agent defined in AAIF can be validated offline, committed to version control, independently audited, and imported into any conforming runtime.

---

**Keywords:** AI agents, multi-agent systems, LLM orchestration, agent portability, interoperability, JSON Schema, Model Context Protocol, OpenTelemetry, compliance, agent state migration, Schema Commons, open standard

---

## 1. Introduction

The modern AI agent is not a simple prompt. A production AI agent encodes a goal, a persona, a set of operational constraints, model preferences with fallback routing across providers, a catalogue of external tools with authentication credentials, memory scopes and retention policies, and compliance obligations that may include data residency requirements, PII handling rules, and human approval gates for irreversible actions. This collection of declarations constitutes the agent's identity and behaviour. In mid-2026, that collection is trapped inside whichever framework created it.

LangGraph represents an agent as a `StateGraph` with a YAML configuration file. CrewAI represents one as a `Crew` composed of `Agent` and `Task` Python class instances. AutoGen uses `AssistantAgent` and `UserProxyAgent` JSON configurations. Open WebUI uses a proprietary "model file" format. The OpenAI Assistants API [10] and Anthropic's agent SDK each define agents through their own hosted API surfaces. The consequence is structural: an agent authored in any one of these environments cannot be imported into any other. There is no shared agent library. There is no cross-platform audit trail. Every migration is a manual reconstruction.

This situation is not new to the software industry, and its trajectory is predictable from historical precedent. Database drivers were incompatible until ODBC established a neutral interface. Electronic mail clients could not exchange messages until SMTP and MIME defined a common encoding. Calendar applications were silos until iCalendar [RFC 5545] provided a portable event format. Container deployments were platform-specific until the OCI image format allowed any conforming runtime to execute any conforming image. In each case, the decisive factor was not the generosity of any vendor but the accumulated cost of incompatibility, which eventually made a neutral standard the rational choice for all parties.

The multi-agent LLM platform market is approaching that inflection point. The cost of fragmentation is no longer merely a developer inconvenience. As AI agents become the primary interface through which organisations execute business processes — querying databases, sending communications, modifying records, triggering workflows — the declarations embedded in an agent definition acquire legal and regulatory weight. An agent that processes EU customer data carries a data residency obligation. An agent that can send emails or post financial transactions requires a human approval gate under many internal control frameworks. An agent that handles personal information carries PII handling requirements under GDPR and analogous regulations.

When those obligations are encoded in a proprietary platform configuration, they are difficult to extract, impossible to share across team boundaries with different tooling, and cannot be audited independently of the platform that created them. This is not a theoretical concern: auditors reviewing AI systems in regulated industries increasingly ask for the agent definition as an artefact. A proprietary binary or Python class structure is not an answer a compliance team can work with.

A vendor-neutral, machine-readable agent definition format resolves all of these problems simultaneously. Such a format allows a developer to define an agent once and import it into any conforming runtime. It allows an auditor to validate the agent's declared constraints and compliance policies offline, without access to the originating platform. It allows the agent to be committed to version control, reviewed in pull requests, diffed between versions, and rolled back. It allows cross-platform migration without manual reconstruction. It makes the agent a first-class software artefact rather than a platform-specific configuration.

This paper presents the Autonomous Agent Interchange Format (AAIF), Schema Commons SC-006 v3.4.0, as a candidate for that role. AAIF is a JSON Schema 2020-12 [4] open standard defining the complete portable declaration of an AI agent. It is published under CC BY 4.0, ships with a reference Python toolchain and conformance test corpus, and supports a self-certification programme that allows platforms to declare compliance without a centralised certifying authority.

The remainder of this paper is organised as follows. Section 2 surveys the current ecosystem and the specific form fragmentation takes. Section 3 presents the seven design principles that motivate AAIF's structure. Section 4 describes the data model in detail. Section 5 covers the conformance model. Section 6 covers capability negotiation and the extension registry. Section 7 situates AAIF in relation to adjacent standards. Section 8 describes the validation and implementation toolchain. Section 9 discusses adoption trajectory and limitations. Section 10 concludes.

---

## 2. Background

By mid-2026, the multi-agent LLM platform ecosystem comprises more than a dozen actively maintained frameworks, each with a proprietary agent representation. Understanding the specific form of this fragmentation is necessary context for evaluating AAIF's design choices.

**LangGraph** (LangChain, Inc.) models agents as directed `StateGraph` instances where nodes are Python functions and edges are conditional transitions. Agent configuration — model choice, tool definitions, memory stores — is expressed through Python class construction and a supplementary YAML configuration layer. There is no canonical export format; a LangGraph agent is defined by its source code.

**CrewAI** models agents as `Agent` Python objects composed into a `Crew` with an ordered list of `Task` definitions. Agent properties including goal, backstory, and tool assignments are constructor arguments. The framework serialises state internally but provides no standard inter-platform document format.

**AutoGen** (Microsoft Research) uses `AssistantAgent` and `UserProxyAgent` objects configured via JSON dictionaries. Group chat topologies are assembled in code. Configuration is partially serialisable but not in a format any other framework can interpret.

**Open WebUI** uses a "model file" format inspired by Ollama's `Modelfile`, encoding system prompts and model parameters in a flat text structure with no native support for tool definitions, memory configuration, or orchestration topology.

**OpenAI Assistants API** [10] represents agents through a hosted API: a system prompt, a list of tools from OpenAI's catalogue, attached files, and a thread-based conversation model. The representation is expressive within its own platform and intentionally bound to it.

**Anthropic's agent SDK** and Google's **Gemini** agent tooling follow the same pattern: rich capabilities within the vendor's own runtime, no portable definition format.

The consequence of this landscape is threefold. First, **no portability**: an agent defined in one framework cannot be imported into another. Second, **no shared library**: organisations cannot share agent definitions across team boundaries using different tooling. Third, **no cross-platform audit**: compliance review of an agent requires access to the originating platform, because the agent's constraints and policies are not expressed in any format that exists independently of it.

An agent's goal, instructions, tools, memory, and constraints are conceptually identical across all of these platforms. The content of what each platform calls its "system prompt," "tool definitions," and "guardrails" is the same thing expressed in incompatible syntaxes. AAIF's starting premise is that the conceptual model is shared; the problem is the absence of a shared document format.

---

## 3. Design Principles

AAIF's data model is shaped by seven design principles stated normatively in SPECIFICATION §B. Each principle addresses a specific failure mode in existing agent representations and motivates concrete field-level design choices described in Section 4.

**1. Declare, don't bind.** Model and tool declarations in an AAIF document express *preferences*, not hard requirements. A consuming runtime MAY substitute equivalent models or tools when the declared ones are unavailable. This is the precondition for portability: a format that hard-codes a specific model identifier or tool endpoint can only be executed on platforms that provide that exact resource. The `model.provider`/`model.preferred`/`model.fallbacks[]` routing chain and the `model.routing_strategy` field implement this principle — they express routing intent rather than binding to a specific deployment endpoint.

**2. Provider-agnostic routing.** Model routing is a first-class concern, not an afterthought. The `model.fallbacks[]` array and `model.routing_strategy` enumeration (preferred\_first, cost, latency, quality, round\_robin) allow an agent definition to express multi-provider routing intent that any conforming platform can fulfil using its available provider integrations. This decouples agent authoring from deployment infrastructure.

**3. Tool-protocol agnostic.** The tool catalogue supports four invocation protocols — `function`, `mcp`, `http`, `openapi` — in a unified tool object. This ensures that agents incorporating Model Context Protocol [8] servers, raw REST endpoints, and OpenAPI-described services can all be represented in a single document. Protocol diversity is a property of the ecosystem; the format must accommodate it without privileging one protocol.

**4. Safety is first-class.** `constraints[]` and `compliance` are normative components, not advisory annotations. A conforming runtime MUST enforce them. This design decision reflects the governance argument in Section 1: if compliance obligations are to be portable, they must be treated as mandatory by the format, not as hints that a runtime may choose to honour. The `safety_level` field governs how aggressively an unsatisfied constraint or capability is handled, from a logged warning (`minimal`) through a hard rejection (`regulated`).

**5. Composable.** AAIF documents can reference other Schema Commons standards via `context[type=schema_ref]` and link to other AAIF agent definitions via `orchestration.subagents[].ref`. This allows multi-agent systems to be expressed as a graph of AAIF definitions, each independently versioned and validated, rather than requiring monolithic agent files.

**6. Verifiable.** `provenance.signature` carries an optional Base64-encoded Ed25519 signature over the canonical JSON of the agent definition. A receiving platform can verify an agent's origin before executing it, providing a chain of custody from author to runtime. This is the basis for trust in cross-organisational agent sharing.

**7. Observable by default.** The `telemetry` block is present in every agent definition and defaults to `tracing: true`. Observability is opt-out, not opt-in. This design choice reflects the operational reality that unobservable agents in production are a support and compliance liability; requiring a positive decision to disable tracing rather than a positive decision to enable it makes the safer default the easier path.

---

## 4. The AAIF Data Model

An AAIF agent definition is a JSON object conforming to `agent.schema.json` (JSON Schema 2020-12 [4]). The top-level object model is:

```
AgentDefinition (root)
├── agent_id          (UUID, assigned once)
├── status            (draft | active | deprecated)
├── tags[]
└── agent
    ├── name / version / description / goal / instructions / skills[]
    ├── model
    │   ├── provider / preferred
    │   ├── provider_id / base_url  ← custom/gateway providers
    │   ├── fallbacks[]             ← multi-provider routing
    │   ├── routing_strategy        ← cost | latency | quality | round_robin
    │   └── params / response_format
    ├── orchestration               ← multi-agent topology
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
    ├── telemetry               ← OTel tracing + metrics
    ├── evaluation              ← LLM-as-judge + test cases
    └── compliance              ← safety_level, data_residency, PII, audit
└── provenance                  ← author, platform, signature
```

The following subsections describe each major component, its field structure, and the rationale for design decisions where non-obvious.

### 4.1 Identity and Lifecycle

Every AAIF document carries a globally unique **`agent_id`** — a UUID v4 [3] assigned at creation and preserved across all import and export operations. Platforms MUST NOT reassign `agent_id` on import; it is the canonical deduplication key and the stable link between an agent definition and any associated agent-state checkpoints (Section 4.8).

The **`status`** field carries one of three lifecycle states: `draft` (under development, not for production execution), `active` (approved and deployable), or `deprecated` (superseded; runtimes SHOULD reject unless explicitly overridden). This lifecycle model allows agent definitions to be managed through a promotion workflow — draft → active — with gating conditions (such as evaluation test case passage) as intermediate steps.

**`agent.version`** is a SemVer string independent of the schema version (`sc_version`). Agent version and schema version are orthogonal: an agent may be at version 2.3.1 while conforming to AAIF schema 3.4.0. This separation allows agent authors to maintain their own versioning discipline without coupling it to schema releases. Breaking changes in agent behaviour (e.g. modified instructions, added constraints) SHOULD increment the major version; backwards-compatible enhancements SHOULD increment the minor version.

### 4.2 LLM Provider Routing

The `model` block implements the declare-don't-bind and provider-agnostic principles. **`model.provider`** identifies the LLM provider from 16 enumerated values: `openai`, `anthropic`, `google`, `vertex_ai`, `mistral`, `cohere`, `groq`, `ollama`, `azure_openai`, `bedrock`, `huggingface`, `together`, `fireworks`, `deepseek`, `xai`, `openrouter`. A `custom` escape hatch accommodates any provider not enumerated — GitHub Copilot, self-hosted LiteLLM or vLLM proxies, Cline-routed endpoints — via `provider_id` (a stable string identifier) and `base_url` (an OpenAI-compatible API endpoint).

**`model.preferred`** names the preferred model in provider notation (e.g. `claude-haiku-3-5`, `gpt-4o-mini`). **`model.fallbacks[]`** is an ordered array of `{provider, model, max_cost_usd_per_1k_tokens}` entries. A conforming runtime walks this chain in order when the preferred model is unavailable or rate-limited. The optional `max_cost_usd_per_1k_tokens` field allows cost-sensitive agents to cap expenditure at the fallback level.

**`model.routing_strategy`** expresses the platform's optimisation objective when multiple models are equally available: `preferred_first` (always try the declared order), `cost` (select the cheapest model meeting `min_context_tokens`), `latency` (select by observed p50 latency), `quality` (select by platform-defined benchmark score), or `round_robin` (distribute load evenly). This level of abstraction — routing intent rather than a model binding — is the correct level for a portable format, because it allows the platform to fulfil the intent using its own available infrastructure rather than requiring a specific deployment to exist.

**`model.params.extended`** (introduced in v2.1) is a free-form pass-through object for provider-specific parameters not covered by the standard fields. For example, Anthropic's extended thinking API accepts `{"thinking": {"type": "enabled", "budget_tokens": 5000}}`; this can be passed via `params.extended` without requiring a schema change. Runtimes forward these parameters verbatim to the provider API and strip them gracefully when routing to a provider that does not support them.

### 4.3 Multi-Agent Orchestration Topology

The `orchestration` block is AAIF's representation of the structural relationships between agents in a multi-agent system. **`orchestration.role`** declares one of five roles: `orchestrator` (coordinates and delegates), `worker` (executes a bounded task), `evaluator` (scores or validates another agent's output), `router` (dispatches to specialists based on input), or `synthesizer` (merges parallel outputs into a unified result).

AAIF supports four topology patterns that cover the observed range of production multi-agent architectures:

```
1. Sequential pipeline      [A] → [B] → [C] → [D]

2. Parallel swarm           [Orchestrator]─┬─[Worker A]─┐
   (fan-out / fan-in)                      ├─[Worker B]─┤─[Synthesizer]
                                           └─[Worker C]─┘

3. Dynamic routing          [Router]─when:X──→[Specialist A]
                                    ─when:Y──→[Specialist B]

4. Mid-run handoff          [Agent A]─condition──→[Agent B]
```

Sequential pipelines are declared via **`orchestration.pipeline[]`** — an ordered list of subagent aliases executed in series, where each agent's output becomes the next agent's input. Parallel swarms are declared by setting **`orchestration.parallel_execution: true`** and listing workers in **`orchestration.subagents[]`**; the runtime fans out to all workers simultaneously and a synthesizer role agent merges the results. Dynamic routing is declared by an agent with `role: "router"` whose `subagents[]` entries carry `when` Condition expressions (Section 6). Mid-run handoffs are declared via **`orchestration.handoff[]`**, each entry specifying a Condition, a target agent reference, and flags for whether context and memory are passed.

**`orchestration.max_iterations`** is a loop guard defaulting to 10; runtimes MUST enforce it to prevent runaway agentic loops. **`orchestration.consensus`** supports agreement mechanisms for parallel outputs: `majority_vote`, `best_of_n`, `referee` (delegating the decision to a named evaluator agent), and `first_success`.

These patterns compose: a pipeline step may itself be a swarm, and a swarm worker may trigger a handoff. The `role` field tells the executing runtime how to interpret the agent's orchestration configuration.

### 4.4 Tool Definitions

The `tools[]` array is a catalogue of every external capability the agent may invoke. Each entry carries a **`protocol`** discriminator (`function`, `mcp`, `http`, `openapi`) that determines how the runtime invokes the tool.

- `function`: an in-process callable, forwarded as-is to the model's function-calling API (OpenAI, Anthropic, or Gemini format)
- `mcp`: a Model Context Protocol [8] server resource, addressed as `mcp://<server>/<capability>`
- `http`: a raw REST endpoint, invoked by the runtime using `parameters_schema` as the request body schema
- `openapi`: an OpenAPI 3.x specification document from which the runtime extracts and exposes operations

**`parameters_schema`** and **`output_schema`** are JSON Schema objects defining the tool's input and output contracts, compatible with OpenAI and Anthropic function-calling formats. **`rate_limit`** and **`cache_ttl_seconds`** allow per-tool throttling and response caching to be declared as part of the agent definition rather than configured separately in each runtime.

**`auth`** is the security-critical component. Authentication type is one of `bearer`, `api_key`, `oauth2`, or `aws_sigv4`. Credentials are referenced, never embedded: `auth.env_var` names an environment variable that the runtime resolves at execution time; the value MUST NOT appear in the AAIF document itself.

**`auth.vault_ref`** (v2.1) is the production-secure form. It carries `{provider, path, key, version}` addressing a secret in an external vault: AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, GCP Secret Manager, or 1Password. The runtime resolves the secret at execution time using its own configured vault credentials; the secret value is never present in the AAIF document at any point. Both `env_var` and `vault_ref` may be declared; `vault_ref` takes precedence. This design reflects the operational reality that production agents run against secrets managed in enterprise vault systems, and a portable format must be able to reference them without embedding values.

### 4.5 Memory Configuration

The `memory[]` array declares the agent's memory requirements across four scopes:

- **`user`**: persists across sessions for a specific user; MUST NOT be shared across users
- **`session`**: persists for the duration of a session; MUST NOT persist beyond the session boundary
- **`task`**: scoped to a single agent run; discarded on completion
- **`long_term`**: persistent, durable storage for facts and history that outlive sessions

Scope is not merely a performance hint — it is a privacy boundary. A runtime MUST NOT persist `scope=session` memory items beyond the session boundary. This is a normative requirement, not a recommendation, because session memory may contain sensitive conversational content not intended for long-term retention.

**`backend`** identifies the storage implementation from eight options: `in_memory`, `redis`, `postgres`, `sqlite`, `pinecone`, `weaviate`, `qdrant`, `chroma`. An importing platform selects a compatible store from those it provides; the scope, key, and retrieval configuration remain constant. For vector backends, **`embedding_model`** and **`retrieval_strategy`** (`similarity`, `keyword`, `hybrid`, `recency`) and **`top_k`** configure the retrieval pipeline. A `custom` escape hatch accommodates backends not enumerated, registered via the community extension registry (Section 6).

### 4.6 Runtime, Telemetry, and Evaluation

**Runtime configuration** provides operators with the controls needed for safe production deployment. `runtime.timeout_seconds` is a hard wall-clock limit; runtimes MUST abort execution after this duration and return an error. `runtime.concurrency` caps the number of simultaneous instances. `runtime.retry_backoff` (`fixed`, `linear`, `exponential`) governs automatic retry behaviour. `runtime.async_execution` and `runtime.queue` support background execution returning a job ID.

**Telemetry** is configured in the `telemetry` block. `telemetry.tracing: true` (the default) instructs the runtime to emit OpenTelemetry spans. Runtimes SHOULD follow the **OpenTelemetry GenAI semantic conventions** [11] for span attribute semantics — the `gen_ai.*` attribute vocabulary and the `invoke_agent`/`chat`/`execute_tool` span hierarchy already emitted by LangChain, CrewAI, AutoGen, and AG2, and natively consumed by Datadog, Honeycomb, and New Relic. **OpenInference** [12] (Arize's OTel-based convention with ten span kinds: LLM, EMBEDDING, RETRIEVER, RERANKER, TOOL, CHAIN, AGENT, GUARDRAIL, EVALUATOR, PROMPT) is an acceptable alternative for runtimes already instrumented with it. AAIF deliberately defers span semantics to these existing conventions rather than defining a third competing vocabulary; the `telemetry.otlp_endpoint` field points the runtime at the collector. `telemetry.metrics: true` enables Prometheus-compatible metrics emission.

**Evaluation** implements LLM-as-judge quality gating. `evaluation.judge_model` names the model used for evaluation (which SHOULD be of equal or greater quality than the agent model). `evaluation.metrics[]` carries threshold-gated metric entries from a vocabulary of nine standard types: `faithfulness`, `relevance`, `coherence`, `toxicity`, `hallucination_rate`, `task_completion`, `latency_ms`, `cost_usd_per_run`, `tool_call_accuracy`. `evaluation.test_cases[]` is a golden test set — `{id, input, expected_output, criteria}` — that the runtime runs against the agent and scores with the judge model. This enables CI/CD gating: a platform SHOULD run the test suite before promoting an agent from `status: "draft"` to `status: "active"`, failing the promotion if any metric threshold is not met.

### 4.7 Compliance Controls

The `compliance` block encodes the agent's regulatory and operational obligations as first-class, normative declarations.

**`safety_level`** is one of four values: `permissive` (minimal enforcement; unsatisfied capabilities log and continue), `standard` (features disabled with operator warnings), `strict` (hard rejection of unsatisfied capabilities or constraints), `regulated` (rejection with mandatory audit logging of the failure). This graduated scale allows agents to declare their own enforcement posture.

**`data_residency`** restricts model routing to providers with data centres in the declared region: `EU`, `US`, `UK`, `APAC`, `global`, or `custom`. A conforming runtime MUST NOT route to a provider outside the declared region. This is an enforceable constraint, not a preference: routing compliance MUST be verified against the provider's documented data processing geography.

**`pii_handling`** declares one of: `none` (no PII expected), `detect` (flag PII in inputs and outputs for logging), `anonymize` (redact PII before passing to the model), `encrypt` (encrypt PII at rest and in transit), `reject` (abort if PII is detected in input). Runtimes MUST apply this policy.

**`audit_log: true`** requires the runtime to maintain an append-only, tamper-evident log of all agent invocations, tool calls, and compliance-relevant events.

**`human_in_the_loop`** (`{enabled, trigger, timeout_seconds}`) installs an approval gate. When `enabled: true`, the runtime MUST pause before any action matching the `trigger` Condition and require explicit human approval before proceeding. `timeout_seconds` defines how long the runtime waits before escalating or aborting. This field is the declarative equivalent of LangGraph's `interrupt()` mechanism, expressed portably.

The placement of these controls in the agent definition rather than deployment configuration is a deliberate design choice. Compliance obligations are properties of the agent — they derive from the data it processes and the actions it takes — not of the platform it runs on. An agent that processes EU customer data carries that obligation regardless of which runtime executes it. A portable format must make that obligation portable.

### 4.8 Agent State Checkpoints

AAIF v3 introduces a companion schema, **`agent-state.schema.json`**, for capturing the complete execution state of a running agent as a portable checkpoint document. This enables three use cases: pause and resume of a running agent, cross-platform live migration (moving an in-flight agent from one runtime to another), and crash recovery from the last checkpoint.

The Agent State document carries:

| Field | Description |
|-------|-------------|
| `state_id` | Unique UUID per checkpoint; new per capture even for the same run |
| `run_id` | Groups all checkpoints for one execution run |
| `agent_id` | Links to the agent definition (`agent.schema.json`) |
| `status` | `running` / `paused` / `awaiting_approval` / `awaiting_tool_result` / `completed` / `failed` / `migrating` |
| `conversation[]` | Full message history (role, content, tool call IDs, token counts, timestamps) |
| `memory_snapshot[]` | All in-scope memory items; vector embeddings are NOT serialised — re-computed on restore |
| `pending_tool_calls[]` | In-flight or queued tool calls with status and callback URLs |
| `subagent_states[]` | Per-subagent summaries; active subagents export their own Agent State documents for deep migration |
| `pipeline_position` | Current step, completed steps, remaining steps, parallel slot |
| `provenance.checksum` | SHA-256 hex digest of the canonical JSON (excluding the checksum field); the receiving platform MUST verify it before restoring |

The **7-step migration protocol** is:

1. Source platform captures Agent State (`status: "paused"` or `"migrating"`)
2. Source platform issues a short-lived, signed migration token (expiry ≤ 15 minutes)
3. Agent State document is transferred to the receiving platform (out-of-band: API, file, message queue)
4. Receiving platform verifies: checksum, migration token, and that `agent_id` matches a known agent definition
5. Receiving platform imports state: loads memory, restores conversation, resumes at `pipeline_position.current_step`
6. Receiving platform re-issues any pending tool calls still in flight, or marks them timed out
7. Execution resumes

For live handoffs where execution must continue without interruption mid-generation, AAIF v3 also specifies a streaming wire format using NDJSON with media type `application/x-aaif-handoff+ndjson`. The stream carries typed messages (`handoff_init`, `context_chunk`, `memory_item`, `pipeline_state`, `pending_tool`, `handoff_complete`, `handoff_error`) and closes with a SHA-256 checksum over the reconstructed Agent State that the receiving platform MUST verify before resuming execution. The stream MUST be transmitted over TLS.

It is important to distinguish AAIF's Agent State from the storage-layer concern addressed by draft-gaikwad-aps-profile-00 [13] (APS). APS specifies a storage service class — an "AgentPersistentState" usage class with CSI/Kubernetes PVC bindings — for a storage backend to advertise itself as suitable for hosting agent state, with crash-consistency, cryptographic erasure, and vector-index workload properties. AAIF's `agent-state.schema.json` specifies the *application-level checkpoint document* — the portable artefact captured from a running agent. These are complementary layers: an AAIF Agent State document is precisely the kind of payload that could be persisted on an APS-class storage volume. AAIF takes no position on the storage layer beneath a checkpoint; APS takes no position on the document format stored in it.

A representative excerpt from the `invoice-chaser.json` example illustrates the key fields of an agent definition:

```json
{
  "sc_standard": "SC-006",
  "sc_version": "2.1.0",
  "agent_id": "a1b2c3d4-0001-4000-8000-invoice000001",
  "status": "active",
  "agent": {
    "name": "Invoice Chaser",
    "version": "1.2.0",
    "goal": "Reduce days-sales-outstanding by chasing overdue invoices.",
    "model": {
      "provider": "anthropic",
      "preferred": "claude-haiku-3-5",
      "fallbacks": [
        { "provider": "openai",  "model": "gpt-4o-mini" },
        { "provider": "groq",    "model": "llama-3.3-70b-versatile" }
      ],
      "routing_strategy": "cost"
    },
    "tools": [
      {
        "name": "list_overdue_invoices",
        "protocol": "mcp",
        "endpoint": "mcp://accounting/invoices",
        "auth": { "type": "bearer", "env_var": "ACCOUNTING_API_TOKEN" }
      },
      {
        "name": "send_email",
        "protocol": "http",
        "endpoint": "https://api.sendgrid.example.com/v3/mail/send",
        "auth": { "type": "bearer", "env_var": "SENDGRID_API_KEY" },
        "rate_limit": { "requests_per_minute": 60 }
      }
    ],
    "memory": [
      { "scope": "long_term", "key": "reminder_log", "backend": "postgres" },
      { "scope": "session",   "key": "run_summary",  "backend": "in_memory" }
    ],
    "compliance": {
      "safety_level": "standard",
      "data_residency": "EU",
      "pii_handling": "detect",
      "audit_log": true
    }
  }
}
```

---

## 5. Conformance Model

AAIF defines seven cumulative conformance levels (§M of the specification). Each level is a superset of the one below it. Conformance is declared per level and per direction (Producer, Consumer, or Both):

- **Producer** at level L: every AAIF document the platform exports validates against `agent.schema.json` and satisfies the level-L predicates.
- **Consumer** at level L: the platform imports and honours every construct required at level L, including all normative MUSTs.

| Level | Direction | Requirements |
|-------|-----------|-------------|
| **Core** | Both | Valid schema; `agent.name` and `agent.goal` present |
| **Tooled** | Both | Core + at least one tool with `parameters_schema` |
| **Portable** | Both | Tooled + `constraints[]` non-empty + resolvable `tools[].endpoint` |
| **Multi-agent** | Both | Portable + `orchestration.role` declared + at least one `subagents[]` or `handoff[]` |
| **Observable** | Both | Portable + `telemetry.tracing: true` + at least one `evaluation.metrics[]` entry |
| **Enterprise** | Both | Observable + `compliance.safety_level` declared + `compliance.audit_log: true` + `provenance.signature` present |
| **Stateful** *(advanced)* | Both | Enterprise + `required_capabilities[]` declared + `state.checkpoint` capability + Agent State checkpoints supported |

The levels are cumulative, but platforms need not climb to the top. The bulk of AAIF's value — portable definitions, provider routing, tool and memory interchange, compliance encoding — is delivered at **Portable** through **Enterprise**, all expressible in the static `agent.schema.json`. **Stateful** is a deliberately separate advanced tier that pulls in the v3 live-state surface: Agent State checkpoints, the cross-platform migration protocol, and the NDJSON streaming handoff wire format. A runtime SHOULD reach Enterprise conformance first and adopt Stateful only when live pause/resume or cross-runtime migration is an actual requirement. Claiming Enterprise conformance is meaningful on its own.

The **self-certification model** mirrors established practice in HTML5 and OCI conformance. There is no central certifying authority; credibility comes from the conformance claim being machine-checkable against the public test corpus. A platform runs the normative conformance test suite at `tests/conformance/` (every fixture in `valid/` MUST validate; every fixture in `invalid/` MUST be rejected), then publishes a machine-readable **Conformance Report** validating against `schema/conformance-report.schema.json` at the well-known path `/.well-known/aaif-conformance.json`. The report states the claimed level, direction, supported AAIF versions, test suite results, and supported registry values. Orchestrators and the ADOPTERS registry consume it for automated platform matching.

Self-certification is a machine-checkable public claim, not a paid certification or an endorsement by the Schema Commons Working Group. It is meaningful precisely because the test suite is public and reproducible: any third party can re-run the suite against the platform's outputs and verify the claim independently.

---

## 6. Capability Negotiation and Extension

### Capability Negotiation

**`agent.required_capabilities[]`** (v2.1) declares the runtime features the agent requires in a dot-namespaced string vocabulary (§R of the specification). Examples include `tool.mcp`, `memory.vector`, `memory.redis`, `orchestration.parallel`, `orchestration.handoff`, `compliance.data_residency`, `compliance.hitl`, `auth.vault`, `state.checkpoint`, and `state.restore`. A conforming platform MUST verify all declared capabilities before accepting an agent definition.

The platform's available capabilities are published in a **Platform Manifest** (`schema/platform-manifest.schema.json`) at `/.well-known/aaif-manifest.json`. An orchestrator can fetch this manifest and perform capability negotiation before dispatching an agent, avoiding silent runtime failures. When a required capability is unsatisfied, the platform's response is governed by the agent's `compliance.safety_level`: `minimal` and `standard` levels may import with degraded functionality and a warning; `strict` and `regulated` levels MUST reject the import with a structured error listing unsatisfied capabilities. Silent capability stripping is a conformance violation.

### Extension Registries

AAIF's design recognises that several extension points — LLM providers, memory backends, tool protocols, vault providers, condition languages, runtime capabilities — will expand faster than a versioned schema can track. Rather than requiring a schema version bump for every new value, AAIF adopts an IANA-style community registry model (§X of the specification).

Six registries are maintained under `registries/`, each a machine-readable JSON file validated against `registries/registry.schema.json`:

| Registry | Extension point | Policy |
|----------|-----------------|--------|
| `providers.json` | `model.provider` | Specification Required |
| `capabilities.json` | `required_capabilities[]` | Expert Review |
| `condition-languages.json` | Condition `lang` | Specification Required |
| `vault-providers.json` | `auth.vault_ref.provider` | Specification Required |
| `memory-backends.json` | `memory[].backend` | Specification Required |
| `tool-protocols.json` | `tools[].protocol` | Standards Action |

The schema enums for each extension point are a **convenience subset**, not a closed world — they are required by the CI harness to be a strict subset of the `status: "standard"` entries in the corresponding registry. A value registered as `standard` but not yet in the schema `enum` is conformant; runtimes SHOULD accept it. The schema enum is widened to match the registry on the next MINOR release; the registry is authoritative in the interim.

New entries are added by community pull request (no schema version bump required), default status `provisional`, with lazy consensus: no Editor objection within 14 days constitutes acceptance. Registration policies range from First Come First Served (unique id + description) through Expert Review (sign-off that the entry is orthogonal and well-scoped). Experimentation requires no registration: the `provider: "custom"` + `provider_id` escape hatch and the `x-` extension namespace (§W) are always valid for unregistered values.

The **`x-*` extension namespace** reserves any property beginning with `x-` at the document root of all three schemas for vendor- or tool-specific metadata. A conforming runtime MUST ignore unrecognised extension keys and MUST NOT let them change agent behaviour. Tooling that re-serialises a document SHOULD round-trip unknown `x-*` keys unchanged.

---

## 7. Related Work

AAIF sits within a broader ecosystem of standards and frameworks for AI agent systems. Understanding AAIF's relationship to adjacent work is necessary for assessing its scope and avoiding mischaracterisation.

### Model Context Protocol [MCP, 8]

The Model Context Protocol, introduced by Anthropic in late 2024, standardises how AI agents invoke external tools and resources — a client-server protocol for tool invocation over HTTP/SSE or stdio, with a JSON-RPC message format. MCP addresses *how* an agent calls a tool; AAIF addresses *what the agent is*. The two are explicitly complementary: AAIF incorporates MCP as one of four tool protocols (`tools[].protocol: "mcp"`), and an AAIF tool definition with `protocol: "mcp"` carries the MCP server endpoint and authentication configuration. AAIF is not competing with MCP; it sits above MCP as the agent's portable blueprint, which includes a reference to MCP servers among its tool catalogue.

### A2A and Agent Cards [A2A, 9]

Google's Agent2Agent (A2A) protocol, proposed in April 2025, defines a wire format for agent-to-agent communication and introduces the **Agent Card** — a minimal discovery document advertising an agent's capabilities (identity, supported input/output modalities, capability tags, and a service endpoint). The Agent Card is the closest existing artefact to what AAIF describes, and it is deliberately thin by design. An AAIF definition can generate a conformant Agent Card from its identity and `skills[]` fields. AAIF sits above A2A's wire protocol and discovery layer as the complete agent definition that a sending agent's runtime would consult before initiating an A2A interaction. The distinction is similar to that between an HTTP endpoint description and the full software specification of the service behind it.

### OpenAI Assistants API [OPENAI-ASSISTANTS, 10]

The OpenAI Assistants API defines agents through a vendor-specific hosted format: a system prompt, a catalogue of OpenAI-provided tools, attached files, and a thread-based conversation model. It is expressive within its platform and not portable outside it. AAIF provides a bidirectional reference converter (`tools/aaif/`) that round-trips agents between AAIF and the OpenAI Assistants format, with a test harness (`tools/test_roundtrip.py`) that verifies lossless conversion. This converter serves as a proof of portability: if AAIF can faithfully represent and restore an OpenAI Assistant, it is expressive enough to capture the information model of the leading production agent platform.

### LangGraph, CrewAI, AutoGen

These three frameworks, described in Section 2, collectively constitute the fragmentation problem AAIF addresses. They share no interchange format. AAIF ships one-way exporters for each in the reference toolchain (`tools/aaif/`). The exporters are partial by design — not all LangGraph StateGraph structures have direct AAIF equivalents — but they handle the core fields (goal, instructions, tools, constraints, model preferences) and log unmapped constructs explicitly. The exporters are the starting point for cross-framework migration workflows, not a complete automation of migration.

### OpenTelemetry GenAI Semantic Conventions [OTEL-GENAI, 11]

The OpenTelemetry GenAI semantic conventions define the `gen_ai.*` span attribute vocabulary and a `invoke_agent`/`chat`/`execute_tool` span hierarchy for generative AI observability. AAIF's `telemetry` block defers span-attribute semantics to OTel GenAI semconv rather than defining its own vocabulary. This design choice reflects the principle that AAIF should be the agent-definition layer, not the telemetry-instrumentation layer — a separate concern that OTel GenAI semconv already addresses with real ecosystem support from LangChain, CrewAI, AutoGen, Datadog, Honeycomb, and New Relic. AAIF configures *whether and where* to send telemetry; OTel GenAI semconv governs *what the spans look like*.

### OpenInference [OPENINFERENCE, 12]

OpenInference, developed by Arize AI, is an OTel-based semantic convention for LLM observability with ten span kinds (LLM, EMBEDDING, RETRIEVER, RERANKER, TOOL, CHAIN, AGENT, GUARDRAIL, EVALUATOR, PROMPT). It covers the same ground as OTel GenAI semconv with a different span model. AAIF does not mandate one over the other; runtimes already instrumented with OpenInference are conformant with AAIF's telemetry requirements. The flexibility reflects the early-stage state of GenAI observability conventions: both are used in production, and AAIF should not create a third option.

### draft-gaikwad-aps-profile-00 [APS, 13]

This IETF individual draft addresses the storage-service layer for agent state: a profile specifying how a storage backend advertises itself as suitable for hosting agent state, with non-normative bindings to SNIA Swordfish/Redfish storage management standards, Kubernetes/CSI integration, crash consistency, and cryptographic erasure tied to identity. APS is about the *volume* that stores agent state; AAIF's `agent-state.schema.json` is about the *document* that is stored. As elaborated in Section 4.8, these are complementary layers. AAIF's agent-state checkpoint document is precisely the kind of payload that an APS-class volume is designed to host. Neither standard depends on or competes with the other.

### Historical Analogues: OCSF, iCalendar, OCI

The Open Cybersecurity Schema Framework [OCSF, 14] provides a useful recent precedent for AAIF's positioning. OCSF launched as a public draft in August 2022; AWS, Splunk, IBM, and Palo Alto Networks publicly committed support within six months. The adoption driver was not technical elegance but the operational cost of auditing heterogeneous telemetry pipelines — the same cost structure that makes proprietary agent definitions a governance problem. iCalendar [RFC 5545, 15] illustrates a different adoption trajectory: specified in 1998, not widely adopted until calendar applications with large user bases (Google Calendar, 2006) implemented it. The OCI image format resolved container deployment fragmentation through a combination of specification quality and Docker's dominant market position. The common thread is that format convergence follows cost accumulation, not specification quality alone. AAIF's technical quality is a necessary but not sufficient condition for adoption.

---

## 8. Validation and Implementation

### Schema Artefacts

AAIF ships four JSON Schema 2020-12 documents:

- **`schema/agent.schema.json`** — the primary agent definition schema (sc_version 3.4.0). `additionalProperties: false` throughout, catching typos and forward-compatibility breaks at validation time, with the `x-*` extension namespace as the managed escape hatch.
- **`schema/agent-state.schema.json`** — the companion checkpoint schema for live state, pause/resume, and migration (sc_version 3.4.0).
- **`schema/platform-manifest.schema.json`** — the platform capability advertisement schema, consumed by orchestrators for pre-dispatch capability negotiation (introduced in v3.1).
- **`schema/conformance-report.schema.json`** — the self-certification report schema, published by platforms at `/.well-known/aaif-conformance.json`.

All four schemas are versioned together under the `sc_version` field and validated in CI.

### Reference Python Toolchain

The reference implementation is a Python package in `tools/aaif/` providing four operations:

```bash
PYTHONPATH=tools python -m aaif validate examples/invoice-chaser.json
PYTHONPATH=tools python -m aaif convert  examples/invoice-chaser.json --target openai_assistant
PYTHONPATH=tools python -m aaif import   my-assistant.json --source openai_assistant
python tools/test_conformance.py SC-006-agent-interchange-format
```

The **bidirectional OpenAI Assistants converter** (`tools/aaif/`) round-trips agent definitions between AAIF and the OpenAI Assistants format. The test harness `tools/test_roundtrip.py` verifies that an Assistant exported to AAIF and re-imported as an Assistant produces an equivalent object, providing machine-verified evidence of format expressiveness. One-way exporters for LangGraph, CrewAI, and AutoGen are also included; they handle the core fields and log unmapped constructs with explicit diagnostic messages.

### Conformance Test Corpus

The normative test corpus at `tests/conformance/` contains two directories:

- `valid/`: fixture files that MUST validate against `agent.schema.json`. These cover Core through Stateful conformance level requirements.
- `invalid/`: fixture files that MUST be rejected with a validation error corresponding to the specific rule they violate. Fixtures are designed to test real rule violations, not annotation-stripping side effects (the `x-sc-schema` extension key is schema-legal, so a fixture is only in `invalid/` if it violates a normative constraint).

`tools/test_conformance.py` runs the full corpus and reports pass/fail per fixture with structured output. `tools/test_registries.py` verifies that the schema enums are subsets of the corresponding registry `status: "standard"` entries.

### Distribution and Editor Support

SchemaStore registration (`schemastore.org`) is a planned near-term distribution step. Registration would provide automatic JSON Schema association in VS Code, JetBrains IDEs, and any editor with SchemaStore support, delivering inline autocomplete and validation for AAIF documents with no per-user configuration. This has historically been an effective zero-cost distribution channel for JSON-based standards.

**Current state of implementation:** the Python toolchain and test corpus exist. Multi-language implementations (TypeScript, Go) and formal working group formation are next steps, not current state. This paper reports honest status, not aspirational claims.

---

## 9. Discussion

### Adoption Trajectory

AAIF v3.4.0 is specification-complete. The four schemas validate, the reference examples pass, the conformance test corpus runs, the OpenAI Assistants round-trip converter works. The gap between a complete specification and a de-facto standard is the normal early-lifecycle state: reference implementations in multiple languages, independent adopters outside the authoring organisation, and time for the ecosystem to discover and evaluate the standard.

Historical precedent suggests that adoption acceleration requires several specific conditions to be met: (a) native AAIF export from at least one major framework — even a partial exporter from LangGraph or CrewAI would establish that the format is implementable by others; (b) a public validation endpoint at a stable URL, enabling CI/CD integration without local toolchain installation; (c) SchemaStore registration, providing editor autocomplete distribution; (d) working group formation with contributors from independent organisations. None of these requires changes to the specification; all are ecosystem and community steps.

### Limitations

**`compliance.data_residency` is a declaration, not enforcement.** AAIF can express that an agent requires EU data residency; it cannot force a runtime to honour that requirement. Enforcement depends entirely on the runtime's implementation — routing logic that verifies the selected provider's data processing geography before making an API call. AAIF provides the vocabulary and the normative obligation; the runtime provides the enforcement mechanism. In regulated environments, the conformance report and audit log provide the evidence trail for an auditor, but the underlying enforcement is always runtime-side.

**`required_capabilities[]` matching is only as reliable as platform manifests.** Capability negotiation is predicated on platforms publishing accurate and complete manifests at `/.well-known/aaif-manifest.json`. A platform that advertises a capability it does not fully implement creates a silent failure mode. The self-certification programme mitigates this by requiring test corpus evidence, but the test corpus cannot cover every possible capability interaction. Operators should treat capability negotiation as a necessary but not sufficient check, particularly for high-stakes deployments.

**The string Condition form is non-deterministic.** Bare string conditions in `orchestration.subagents[].when` and `orchestration.handoff[].condition` are natural-language hints evaluated differently by each runtime. They are permitted for backward compatibility and authoring convenience, but agents targeting Portable conformance or above SHOULD use the structured Condition form (`{lang, expr, nl}`) for any condition affecting control flow. AAIF's specification (§V) emits a portability warning for agents routing on string conditions.

### Relation to the Emerging Agent Stack

AAIF addresses the agent-definition layer. It is designed to compose with adjacent standards addressing other layers of the multi-agent portability problem. AAIF (agent definition) + SC-013 Agent Registry Protocol [ARP, 6] (discovery and federation of agent definitions) + SC-014 Agent Capability and Profile Model [ACPM, 7] (capability trust, cost profiling, and platform matching) together address a coherent vertical slice of the agent infrastructure problem: how an agent is defined, how it is discovered, and how its capabilities and costs are communicated to orchestrators and operators. Each of these standards is independently useful and independently citable; the value of composition is that a platform implementing all three can offer end-to-end agent lifecycle management across heterogeneous runtimes.

---

## 10. Conclusion

The multi-agent LLM platform ecosystem lacks a portable, vendor-neutral format for AI agent definitions. An agent's goal, instructions, model preferences, tool catalogue, memory configuration, and compliance obligations are today encoded in framework-specific proprietary representations that cannot be migrated without manual reconstruction and cannot be audited independently of the originating platform. As AI agents encode compliance obligations with regulatory weight — data residency, PII handling, human approval gates — this fragmentation is not merely a developer inconvenience but a governance gap.

AAIF v3.4.0 (Schema Commons SC-006) addresses this gap through a JSON Schema 2020-12 open standard covering identity through compliance in a single portable document format. The standard encompasses ten normative components — identity and lifecycle, LLM provider routing with fallback chains, multi-agent orchestration topology, tool definitions with structured authentication and vault-reference secrets management, four-scope memory configuration, runtime policy, OpenTelemetry telemetry, LLM-as-judge evaluation, compliance controls, and cryptographic provenance — together with a companion `agent-state.schema.json` schema enabling live migration of running agents via a 7-step protocol and NDJSON streaming handoff. The standard ships with a conformance self-certification programme, four JSON Schema artefacts, a Python reference toolchain, a bidirectional OpenAI Assistants converter with round-trip verification, and a public test corpus.

The governance significance extends beyond developer convenience. Agent definitions that encode compliance obligations should be portable, versionable, and independently auditable artefacts, not proprietary platform configurations. AAIF provides the vocabulary, the schema, and the conformance programme to make that possible.

Historical precedent from ODBC, iCalendar, and OCI consistently shows that format convergence follows cost accumulation. The question for the AI agent ecosystem is not whether a portable interchange format will emerge, but whether the format that achieves de-facto status will be open and community-governed or vendor-owned. AAIF is a specification-complete, openly licensed candidate for the former.

---

## References

[1] Bradner, S. "Key words for use in RFCs to Indicate Requirement Levels," BCP 14, RFC 2119, March 1997. https://www.rfc-editor.org/rfc/rfc2119

[2] Leiba, B. "Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words," BCP 14, RFC 8174, May 2017. https://www.rfc-editor.org/rfc/rfc8174

[3] Leach, P., Mealling, M., and R. Salz. "A Universally Unique IDentifier (UUID) URN Namespace," RFC 4122, July 2005. https://www.rfc-editor.org/rfc/rfc4122

[4] Wright, A., Andrews, H., Hutton, B., and G. Dennis. "JSON Schema: A Media Type for Describing JSON Documents," IETF Internet-Draft, draft-bhutton-json-schema-01, 2020. https://json-schema.org/specification

[5] van Bussel, B. "Autonomous Agent Interchange Format," Schema Commons SC-006 v3.4.0, Observalytics SL, June 2026. https://github.com/Observalytics-SL/aaif

[6] van Bussel, B. "Agent Registry Protocol," Schema Commons SC-013, Observalytics SL, June 2026.

[7] van Bussel, B. "Agent Capability and Profile Model," Schema Commons SC-014 v1.0.0, Observalytics SL, June 2026.

[8] Anthropic. "Model Context Protocol Specification," anthropic.com, November 2024. https://modelcontextprotocol.io

[9] Google. "Agent2Agent Protocol," a2aprotocol.ai, April 2025. https://a2aprotocol.ai

[10] OpenAI. "Assistants API Reference," platform.openai.com, 2023. https://platform.openai.com/docs/api-reference/assistants

[11] OpenTelemetry Contributors. "Semantic Conventions for Generative AI Systems," opentelemetry.io/docs/specs/semconv/gen-ai/, 2026. https://opentelemetry.io/docs/specs/semconv/gen-ai/

[12] Arize AI. "OpenInference Semantic Conventions," github.com/Arize-ai/openinference, 2026. https://github.com/Arize-ai/openinference

[13] Gaikwad et al. "Agent Persistent State (APS) Profile," IETF Internet-Draft, draft-gaikwad-aps-profile-00, Work in Progress, 2026.

[14] AWS, Splunk et al. "Open Cybersecurity Schema Framework v1.0," github.com/ocsf/ocsf-schema, 2022. https://github.com/ocsf/ocsf-schema

[15] Desruisseaux, B. (ed.) "Internet Calendaring and Scheduling Core Object Specification (iCalendar)," RFC 5545, September 2009. https://www.rfc-editor.org/rfc/rfc5545

---

*Schema Commons SC-006 AAIF v3.4.0 · CC BY 4.0 · June 2026*
*Repository: https://github.com/Observalytics-SL/Frameworks/tree/main/SC-006-agent-interchange-format*
