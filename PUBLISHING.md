# Publishing AAIF — paths to a recognised open standard

AAIF is designed to be published through several complementary channels. None of them are mutually exclusive; together they give the standard academic citability, standards-body legitimacy, and developer reach. This document is the roadmap from "a specification in a repository" to "a standard the field cites and implements."

## 0. Before submitting anywhere: prior-art status and submission readiness

An IETF Internet-Draft becomes public and permanently archived on the Datatracker the instant it is submitted. There is no private or draft-review submission step — once filed, it is citable, indexed, and there forever (even superseded revisions remain visible in the history). Anything that needs fixing belongs in the repository **before** that moment, not after.

The §N "Related Work & Mapping to Prior Art" section of [SPECIFICATION.md](SPECIFICATION.md) reflects the current state of that diligence. The core AAIF claim — that no existing standard defines a portable, vendor-neutral agent *definition* document — held up under a real, targeted search: the closest adjacent efforts (draft-gaikwad-aps-profile-00, OpenTelemetry GenAI semantic conventions, OpenInference, MCP's own roadmap-documented observability gap) all address different layers or different problems, and §N states plainly where each one is complementary rather than competing.

One item needs re-checking before submission rather than being treated as settled: **draft-gaikwad-aps-profile-00** is an active, evolving IETF individual draft touching the adjacent Agent State area. Individual drafts can change shape, get adopted into a working group, or be superseded between revisions. Re-verify its current status and content against §N's characterization immediately before filing, not from this snapshot.

**Submission status: READY FOR INITIAL FILING.** Prior-art diligence is complete (see §N of SPECIFICATION.md). The draft (draft-schemacommons-aaif-00.xml) is clean and submission-ready. Verify the current status of draft-gaikwad-aps-profile-00 on the IETF Datatracker immediately before filing and update §N if the characterisation has changed.

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

AAIF is a **public draft**. It has no external adopters yet; see the honest status note in the [README](README.md). The fastest credibility wins are: (1) mint a DOI, (2) land one independent runtime adopter, (3) post the arXiv whitepaper.
