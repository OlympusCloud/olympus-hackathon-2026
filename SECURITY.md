# Security Policy

## Reporting a vulnerability

Please email **security@nebusai.com** with details. We acknowledge within 2 business days and aim to triage within 5. Do not open public issues for security findings.

## IP / trade-secret hygiene gate

This repo is a deliberate, Apache-2.0 carve-out from the closed Olympus Cloud monorepo. Every file added is reviewed against the criteria below before merge.

### Public-safe (allowed in this repo)

- Ceres node/state shape (graph topology, intent enum, TypedDict field names)
- ADK manifest (node names, conditional edges, tool name references)
- Terraform module for Vertex AI Agent Builder + Memory Bank + IAM (sanitized — no per-env state, no shared-services bindings)
- Minimal Dart sample app using `olympus_sdk` to call the hosted agent
- Architecture documentation, mapping tables, diagrams
- Before/after metric methodology
- License (Apache-2.0), CODEOWNERS, this security policy

### NOT public-safe (forbidden in this repo)

- Ether tier catalog, model weights, cost tables, classifier keyword lists
- Pantheon system prompts (beyond Ceres node/state shape)
- Tool implementations (we name tools in the ADK manifest; we do not ship their bodies)
- Per-environment Terraform state files
- Shared-services account bindings or service-account keys
- Customer data, tenant data, production secrets
- Spanner schemas for proprietary domains
- Source code from the other 26 Pantheon agents

## Review process

Each PR to this repo:

1. Author tags the PR with `ip-review-needed`.
2. Maintainer reviews against the lists above.
3. If any forbidden artifact is present, PR is blocked until the artifact is removed or rewritten to public-safe form.
4. Once cleared, maintainer tags `ip-review-cleared` and merges.

This process satisfies the IP-gate criteria from the private epic that authorized the carve-out.

## License

Apache-2.0 (see [LICENSE](./LICENSE)). Contributors agree their submissions are licensed under the same terms.
