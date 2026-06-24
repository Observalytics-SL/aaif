# AAIF Conformance & Self-Certification

> **How a platform proves it "speaks AAIF."** Conformance is per-level, per-direction, and self-certified against a public test suite — the same model as "valid HTML5" or "OCI-compliant." No gatekeeper; credibility comes from the claim being machine-checkable. Normative rules are in [SPECIFICATION §Y](SPECIFICATION.md); §M defines the levels.

## 1. Pick a level and a direction

**Levels** (cumulative — see [§M](SPECIFICATION.md)): `Core` → `Tooled` → `Portable` → `Multi-agent` → `Observable` → `Enterprise` → `Stateful` *(advanced)*.

**Directions:**
- **Producer** — everything you *export* is valid AAIF at level L.
- **Consumer** — everything you *import* at level L you also **honour** (enforce the level's normative MUSTs, not just parse them).
- **Both.**

> Most platforms should target **Consumer:Portable** or **Consumer:Enterprise** first — that is where portability pays off. Stateful (live migration, streaming handoff) is opt-in.

## 2. Run the public test suite

The normative corpus is [`tests/conformance/`](tests/conformance/): every `valid/` file must validate; every `invalid/` file must be rejected for a real rule violation.

```bash
python -m pip install -r tools/requirements.txt
python tools/test_conformance.py SC-006-agent-interchange-format   # schema corpus
python tools/test_registries.py  SC-006-agent-interchange-format   # registry consistency
python tools/test_roundtrip.py   SC-006-agent-interchange-format   # interop round-trip
```

A **Consumer** claim additionally requires you to demonstrate enforcement of the level's MUSTs. The behavioural checklist:

| Level | A conforming **Consumer** MUST… |
|-------|--------------------------------|
| Core | Reject documents that fail `agent.schema.json`. |
| Tooled | Expose declared tools with their `parameters_schema` to the model. |
| Portable | **Enforce `constraints[]`** (system-prompt + output filter); treat `tools[].endpoint` as untrusted. |
| Multi-agent | Execute the declared topology (`pipeline`/`parallel`/`handoff`) and evaluate structured Conditions (§V) deterministically, or degrade per `safety_level`. |
| Observable | Emit OTEL traces and run `evaluation.metrics[]` gates. |
| Enterprise | Enforce `compliance` (`data_residency`, `pii_handling`, `human_in_the_loop`), write an immutable `audit_log`, and verify `provenance.signature` when present. |
| Stateful | Capture/restore Agent State (§Q); verify `checksum` and `migration_token` before restore. |

Unsupported `required_capabilities[]` or Condition `lang`s MUST be handled per the agent's `safety_level` (§R) — silent stripping is a violation.

## 3. Publish a Conformance Report

Generate a report validating against [`schema/conformance-report.schema.json`](schema/conformance-report.schema.json) and serve it at:

```
https://<your-platform>/.well-known/aaif-conformance.json
```

See [`examples/conformance-report.json`](examples/conformance-report.json) for a complete example. The report declares your claimed levels/directions, the test-suite result, supported registry ids, and an attestation. Orchestrators fetch it (alongside your Platform Manifest, §U) to decide whether to dispatch an agent to you.

## 4. List yourself

Add a row to [ADOPTERS.md](ADOPTERS.md) linking to your `.well-known/aaif-conformance.json`. Listing is self-service and free; the report makes the claim verifiable.

## What self-certification is and isn't

- **Is:** a public, reproducible, machine-checkable statement. Anyone can re-run the suite against your exports or your importer and confirm the claim.
- **Isn't:** a paid certification, a trademark licence, or a guarantee of fitness. The Schema Commons Steering Council MAY ask a platform to correct a demonstrably false claim before it stays listed in ADOPTERS.md.

## Conformance changes between versions

A platform's report names the `aaif_versions` it supports. Because every change is SemVer (see [GOVERNANCE.md](../GOVERNANCE.md)), a MINOR bump never invalidates an existing conformant document; re-certification is only needed to *claim* new MINOR features.
