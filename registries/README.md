# AAIF Extension Registries

> **How AAIF grows without forking.** The core JSON Schema (`schema/agent.schema.json`) deliberately enumerates only a *recommended* set of identifiers. The full, living list of allowed values for each open extension point lives here, as machine-readable registries that the community extends by pull request. New vendors, vault providers, memory backends, or condition languages can be added **without a breaking schema change**.

This is the same mechanism IANA uses to keep IP, MIME, and HTTP registries open and stable for decades. See [SPECIFICATION §X](../SPECIFICATION.md) for the normative rules.

## The registries

| File | Extension point | Registration policy |
|------|-----------------|---------------------|
| [`providers.json`](providers.json) | `model.provider` | Specification Required |
| [`capabilities.json`](capabilities.json) | `required_capabilities[]` / manifest capabilities | Expert Review |
| [`condition-languages.json`](condition-languages.json) | Condition `lang` (§V) | Specification Required |
| [`vault-providers.json`](vault-providers.json) | `auth.vault_ref.provider` | Specification Required |
| [`memory-backends.json`](memory-backends.json) | `memory[].backend` | Specification Required |
| [`tool-protocols.json`](tool-protocols.json) | `tools[].protocol` | Standards Action |

Every file validates against [`registry.schema.json`](registry.schema.json) and is checked in CI by `tools/test_registries.py`.

## Identifier status lifecycle

```
(proposed PR) → provisional → standard → deprecated
                                   reserved
```

- **standard** — ratified; safe to rely on.
- **provisional** — accepted and usable, but the id or semantics may still change. Until a provider id is `standard`, prefer `provider: "custom"` + `provider_id`.
- **deprecated** — retained for backward compatibility; do not use in new documents.
- **reserved** — the name is held (e.g. to avoid a clash) but not yet usable.

## Registration policies (IANA-style)

| Policy | What you must provide |
|--------|-----------------------|
| **First Come First Served** | A unique id and a one-line description. |
| **Specification Required** | The above **plus** a stable public spec/API/docs URL for the thing being registered. |
| **Expert Review** | The above **plus** sign-off from a standard Editor that the entry is orthogonal and well-scoped. |
| **Standards Action** | A change to the normative schema in a new MINOR version (every runtime must implement it). |

## How to register an identifier

1. Add an entry to the relevant `*.json` file (keep entries grouped by `status`, then roughly by maturity).
2. Set `status: "provisional"` unless an Editor is promoting it to `standard`.
3. Fill in the policy-required fields (docs URL, spec link, etc.).
4. Run `python tools/test_registries.py SC-006-agent-interchange-format` — it must pass.
5. Open a PR titled `SC-006: register <registry> id '<id>'`.

Lazy consensus applies (see [GOVERNANCE.md](../../GOVERNANCE.md)): no Editor objection within 14 days = accepted.

## Private / experimental identifiers

You do **not** need to register to experiment. Any value used as `provider: "custom"` + `provider_id`, or any `x-`-prefixed extension key (§W), is valid without registration. Register only when you want interoperability and discoverability across runtimes.
