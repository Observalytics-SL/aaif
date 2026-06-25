# Security Policy — AAIF (SC-006)

AAIF is a data-format standard, but agent definitions describe systems that execute code, call tools, hold secrets, and move state between platforms. Security is therefore in scope for both the **specification** and the **reference tooling**.

## Reporting a vulnerability

- **Reference tooling** (`tools/`, the `aaif` package): report privately to **security@observalytics.com**. Please do not open a public issue for an exploitable bug. We aim to acknowledge within 5 business days and to publish a fix or advisory within 90 days.
- **Specification weaknesses** (a construct that is unsafe by design, an under-specified MUST, a missing guardrail): open a public issue titled `[security] SC-006: <summary>` so it can be discussed and corrected in the open.

Please include: affected file/section or version, a minimal reproducing AAIF document or steps, and the impact you observed.

## Threat model (normative references in SPECIFICATION §L, §Q, §S)

Implementers MUST account for these when consuming AAIF documents from any source they do not fully trust:

| Threat | Mitigation required by the spec |
|--------|---------------------------------|
| **Malicious tool endpoints** | Treat `tools[].endpoint` as untrusted; capability-gate before activation (§L). |
| **Secret exfiltration** | Secret *values* MUST NOT appear in a document; only `auth.env_var` / `auth.vault_ref` references (§D, §L). |
| **Prompt injection via fetched context** | Sandbox/strip `context[type=url]` content fetched at runtime (§L). |
| **Constraint stripping** | Dropping a `constraints[]` entry is a conformance violation (§I, §L). |
| **Unsafe routing on NL conditions** | Prefer deterministic structured Conditions; never route a `strict`/`regulated` agent on an unverifiable hint (§V, §R). |
| **State tampering / replay** | Verify `provenance.checksum` and the signed, short-lived `migration_token` before restoring Agent State (§Q); discard state on `handoff_error` (§S). |
| **Cross-tenant state leakage** | Never restore `scope=session` memory into a different user's session (§Q). |
| **Spoofed origin** | Verify `provenance.signature` before executing an agent from an untrusted source (§L). |
| **Data-residency violation** | Route only to providers in the declared `compliance.data_residency` region (§L). |
| **Supply-chain trust of registries** | Registry entries are advisory identifiers, not executable code; resolving an id to an endpoint still requires the consumer's own capability gating (§X). |

## Scope

In scope: the schemas, the normative spec, and the reference tooling in this repository. Out of scope: third-party runtimes that consume AAIF (report those to their own maintainers), and the security of the external services an agent happens to call.

## Disclosure

We follow coordinated disclosure. Reporters acting in good faith will be credited in the advisory unless they request otherwise.
