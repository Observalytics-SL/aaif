# SC-006 AAIF — Adopter Registry

This file lists organisations and projects that have declared conformance with or use of the Autonomous Agent Interchange Format (AAIF, SC-006).

Listing is **self-service and free**. Add your entry via pull request. No approval required — the list is informational, not a certification.

---

## How to register

Add a row to the table below and open a pull request. The only requirement is that you are genuinely using AAIF in some capacity (production, staging, tools, or active evaluation).

**Conformance levels** (see [SPECIFICATION.md](SPECIFICATION.md) §M):
- `Core` — validates against the schema
- `Tooled` — Core + ≥1 tool with parameters_schema
- `Portable` — Tooled + constraints + resolvable endpoints
- `Multi-agent` — Portable + orchestration declared
- `Observable` — Portable + tracing + evaluation metrics
- `Enterprise` — Observable + compliance + audit log + signature

---

## Adopters

| Organisation / Project | Type | Conformance level | AAIF version | Use case | Since | Link |
|------------------------|------|------------------|-------------|---------|-------|------|
| SWARM (Renegadez) | Enterprise | Enterprise | 3.4.0 | Reference runtime — import/export of personas & playbooks; capability negotiation; conformance endpoint | 2026-06 | https://swarm-software.ai |
| *(your entry here)* | | | | | | |

---

## Template

Copy and fill in:

```
| Acme Corp | Enterprise | Portable | 2.0.0 | Internal agent catalogue for 12 production agents | 2026-07 | https://acme.example.com |
```

**Type options:** `Enterprise`, `Startup`, `Open source`, `Research`, `Individual`

---

## Reference implementations and tooling

If you have built a tool that reads or writes AAIF documents (converter, importer, exporter, validator), list it here:

| Tool / Library | Language | AAIF version | Description | Link |
|----------------|----------|-------------|-------------|------|
| SWARM AAIF adapter | TypeScript | 3.4.0 | Validate (ajv 2020-12) + bidirectional persona/playbook ↔ AAIF with capability negotiation and round-trip; HTTP import/export + conformance endpoint | https://swarm-software.ai |
| `aaif` reference package | Python | 3.4.0 | Validate / info / convert / import; bidirectional OpenAI Assistants round-trip + LangGraph/CrewAI/AutoGen exporters | [tools/aaif/](../tools/aaif/) |
| `schema-commons/validate.py` | Python | 3.4.0 | Reference schema validator | [tools/validate.py](../tools/validate.py) |
| `test_conformance.py` / `test_registries.py` / `test_roundtrip.py` | Python | 3.4.0 | Public conformance, registry-consistency, and interop round-trip suites | [tools/](../tools/) |
| *(your tool here)* | | | | |

### Self-certified conformance reports

Platforms that publish a [conformance report](CONFORMANCE.md) at `/.well-known/aaif-conformance.json` may link it here:

| Platform | Claimed level(s) | Direction | Report |
|----------|------------------|-----------|--------|
| *(your platform here)* | | | `https://…/.well-known/aaif-conformance.json` |

---

## Wanted: first independent adopters

We are actively seeking the first three independent platform adoptions. If you are building or operating a multi-agent LLM platform and would like to add AAIF support, please open an issue titled `[Adoption] <Platform name>`. We will:

- Help map your existing agent format to AAIF
- Co-author a converter if needed
- Credit your platform as a founding adopter in the white paper

Platforms we would most like to see AAIF support in: **Open WebUI**, **LangGraph**, **CrewAI**, **AutoGen**, **Semantic Kernel**, **Haystack**, **BeeAI**.
