# Contributing to AAIF

*Published by [Observalytics SL](https://github.com/Observalytics-SL) — Schema Commons initiative.*

Thank you for your interest in the Autonomous Agent Interchange Format. Contributions of all sizes are welcome — typo fixes, new examples, field proposals, or implementation reports.

## Ways to contribute

- **Fix or clarify** the spec, schema descriptions, or examples.
- **Propose a new field** or enum value (backwards-compatible additions welcomed).
- **Report a validation issue** — if valid real-world data fails the schema, that is a bug.
- **Map an existing format** (LangGraph, AutoGen, CrewAI, Open WebUI…) to AAIF and document the gap.
- **Register as an adopter** — add yourself to [ADOPTERS.md](ADOPTERS.md) via PR.

## Repo layout

```
schema/                   # four JSON Schema 2020-12 files (the source of truth)
  agent.schema.json
  agent-state.schema.json
  platform-manifest.schema.json
  conformance-report.schema.json
examples/                 # at least two valid instances per schema
context.jsonld            # JSON-LD context
SPECIFICATION.md          # full normative specification
CONFORMANCE.md            # conformance levels and test matrix
WHITEPAPER.md             # design rationale and background
draft-schemacommons-aaif-00.xml   # IETF Internet-Draft source
tools/validate.py         # validation helper
```

## Local setup

```bash
python -m pip install jsonschema referencing
python tools/validate.py --all
```

## Quality bar

1. **Schemas validate** — run `python tools/validate.py --all` before opening a PR.
2. **Examples are realistic** — no `foo`/`bar`; use plausible production-like data.
3. **Fields are documented** — every added property needs a `description` in the schema.
4. **No breaking changes** without a major version bump — removing or retyping a required field is a breaking change.
5. **CHANGELOG updated** — add your change to the `[Unreleased]` section of [CHANGELOG.md](CHANGELOG.md).

## IETF Internet-Draft

The IETF draft (`draft-schemacommons-aaif-00.xml`) is maintained by the Schema Commons Steering Council. If your schema change is significant enough to warrant an IETF revision, note it in your PR and it will be queued for the next draft revision. You do not need to edit the XML directly.

## Commit & PR style

- One logical change per PR.
- Title format: `aaif: <short description>` — e.g. `aaif: add gpu_memory field to runtime constraints`.
- Reference the relevant section of SPECIFICATION.md if applicable.
- Keep discussion of design rationale in the PR description; the spec text stays normative and concise.

## Conformance levels

AAIF has seven conformance levels (Core → Tooled → Portable → Multi-agent → Observable → Enterprise → Stateful). If your change adds or removes conformance requirements, update [CONFORMANCE.md](CONFORMANCE.md) accordingly.

## Licence

By contributing you agree your contribution is licensed under **CC BY 4.0** (documentation and schemas) or **Apache 2.0** (tooling), matching the existing licence.
