# Publishing AAIF — paths to a recognised open standard

AAIF is designed to be published through several complementary channels. None of them are mutually exclusive; together they give the standard academic citability, standards-body legitimacy, and developer reach. This document is the roadmap from "a specification in a repository" to "a standard the field cites and implements."

## 0. Before submitting anywhere: prior-art status and submission readiness

An IETF Internet-Draft becomes public and permanently archived on the Datatracker the instant it is submitted. There is no private or draft-review submission step — once filed, it is citable, indexed, and there forever (even superseded revisions remain visible in the history). Anything that needs fixing belongs in the repository **before** that moment, not after.

The §N "Related Work & Mapping to Prior Art" section of [SPECIFICATION.md](SPECIFICATION.md) reflects the current state of that diligence. The core AAIF claim — that no existing standard defines a portable, vendor-neutral agent *definition* document — held up under a real, targeted search: the closest adjacent efforts (draft-gaikwad-aps-profile-00, OpenTelemetry GenAI semantic conventions, OpenInference, MCP's own roadmap-documented observability gap) all address different layers or different problems, and §N states plainly where each one is complementary rather than competing.

**draft-gaikwad-aps-profile-00** was flagged as the closest adjacent work (Agent State area). As of June 2026 it has **expired** on the IETF Datatracker with no WG adoption and no stream assignment. Its scope was Kubernetes-layer storage infrastructure (crash consistency, vector indexing, cryptographic erasure) — different from AAIF's schema-level state capture. The characterisation in §N remains accurate; no update required before filing.

**Submission status: READY FOR INITIAL FILING.** No blocking prior art identified. All individual I-Ds in the adjacent agent-definition, agent-state, and agent-discovery spaces remain unaffiliated individual submissions with no WG home as of June 2026. The draft (draft-schemacommons-aaif-00.xml) is clean and submission-ready.

## 1. Archival + DOI (citable today)

**Goal:** a permanent, versioned, citable artifact for academic and industrial reference.

- [`CITATION.cff`](CITATION.cff) makes the repository citable on GitHub and is consumed by Zenodo.
- Connect the repository to **Zenodo** and cut a tagged release → Zenodo mints a versioned **DOI**. Replace the placeholder DOI in `CITATION.cff`.
- The DOI is what papers, vendor docs, and the IETF draft reference. Each release gets its own DOI; a concept DOI always points at the latest.

## 2. Academic publication (the "PhD" track)

**Goal:** peer-reviewed grounding and a citable paper.

- The [WHITEPAPER.md](WHITEPAPER.md) is the basis for a systems/standards paper. Strong venues: **arXiv (cs.AI / cs.MA / cs.SE)** for immediate availability, then a workshop/conference on agent infrastructure, LLM systems, or interoperability.
- A defensible research contribution is framed three ways: (a) the **portability gap** across runtimes as a measured problem; (b) AAIF as a **formal interchange model** (a typed agent record + a conformance lattice over levels, §M); (c) an **evaluation** — round-trip fidelity across ≥2 real frameworks (`tools/test_roundtrip.py` is the seed of this), and a coverage analysis of existing formats mapped to AAIF (§N).
- Reproducibility: the schemas, conformance corpus, registries, and reference converters in this repo are the artifact appendix.

## 3. IETF Internet-Draft (standards-track legitimacy)

**Goal:** review in an open standards body and a stable, referenceable document series.

- The specification is already structured for this: it uses RFC 2119/8174 normative keywords (§"Terminology"), has **Security Considerations** ([SECURITY.md](SECURITY.md) + §L) and **IANA-style Considerations** (the registries, §X), and a **References** section.
- Reformat `SPECIFICATION.md` into the I-D template (`kramdown-rfc`/`xml2rfc`) as `draft-<editor>-aaif-00`. Submit to the IETF datatracker; seek a home in an AI/agents or applications-area discussion (or an Independent Submission via the ISE).
- The registries in [`registries/`](registries/) become the "IANA Considerations": each file already declares an IANA-style registration policy (Specification Required / Expert Review / Standards Action).

## 4. W3C Community Group (web + semantic-web reach)

**Goal:** multi-stakeholder governance and Linked-Data alignment.

- [`context.jsonld`](context.jsonld) already maps AAIF terms to URIs (schema.org, PROV-O, Dublin Core). A **W3C Community Group** ("Portable AI Agents CG") is a low-barrier home for cross-vendor participation and a future CG Report.

## 5. Reference runtime + adopters (running code)

**Goal:** "rough consensus and running code" — the credibility that matters most.

- The `aaif` reference package (validate / info / convert / import) and the bidirectional OpenAI Assistants round-trip are the seed. Priority next adapters: **LangGraph, CrewAI, AutoGen, Open WebUI, Semantic Kernel** (import + export).
- The **first independent runtime** to implement AAIF is recorded as the reference implementation in [ADOPTERS.md](ADOPTERS.md); platforms self-certify via [CONFORMANCE.md](CONFORMANCE.md).

## Canonical URIs (to reserve)

| Purpose | URI |
|---------|-----|
| Standard landing page | `https://github.com/Observalytics-SL/aaif` |
| Agent schema `$id` | `https://github.com/Observalytics-SL/aaif/agent.schema.json` |
| Versioned schema | `https://github.com/Observalytics-SL/aaif/3.4.0/agent.schema.json` |
| JSON-LD context | `https://raw.githubusercontent.com/Observalytics-SL/aaif/main/context.jsonld` |
| Platform manifest well-known | `/.well-known/aaif-manifest.json` |
| Conformance report well-known | `/.well-known/aaif-conformance.json` |

When the domain is live, schema `$id`s SHOULD resolve to the schema file and SHOULD be content-addressable per version. Until then the `$id`s are stable identifiers, not necessarily dereferenceable URLs.

## Status

AAIF v3.4.0 is a **public draft**. DOI minted (10.5281/zenodo.20845316). IETF Internet-Draft (`draft-schemacommons-aaif-00`) is submission-ready — see above for the Datatracker link. One external adopter listed in [ADOPTERS.md](ADOPTERS.md). arXiv submission and W3C Community Group remain pending.
