# Olympus Hackathon 2026 — NebusAI / Olympus Cloud

**Submission**: Google Cloud for Startups Hackathon 2026
**Track**: Optimize an existing prototype for production
**Submitter**: Scott Houghton (NëbusAI) — single-person team
**Status**: 🚧 in progress; deadline ~June 5, 2026

This repo is the **public, Apache-2.0 carve-out** for the submission. The full Olympus Cloud platform stays private; this repo contains only the artifacts a judge or reader needs to:

- Understand the architecture (mapping + diagram)
- Reproduce the demo (`make demo` after credentials are configured)
- Read the ADK manifest + Terraform we used to port one Pantheon agent to Google's Agent Platform

## What we did

We ported **one Pantheon agent — Ceres (inventory)** — from our LangGraph implementation to **Vertex AI Agent Builder + ADK + Agent Runtime + Agent Memory Bank**, kept Gemini inference routed through our internal Ether cost-tier router, and exposed the hosted agent to a customer Flutter app through `olympus_sdk` with a single method call.

The point: prove the **AI-native PaaS** thesis on Google's stack — a small team shipping an AI-operated workflow on Agent Platform, end-to-end, in 13 days.

## Architecture

```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Customer App    │     │  Olympus        │     │  Vertex AI       │
│  (Flutter)       │────▶│  API Gateway    │────▶│  Agent Runtime   │
│  olympus_sdk     │     │  (Go)           │     │  (Ceres ADK)     │
└──────────────────┘     └─────────────────┘     └────────┬─────────┘
                                                          │
                                          ┌───────────────┼───────────────┐
                                          ▼               ▼               ▼
                                   ┌────────────┐ ┌────────────┐ ┌────────────┐
                                   │  Gemini    │ │  Agent     │ │  Spanner   │
                                   │  via Ether │ │  Memory    │ │  inventory │
                                   │  router    │ │  Bank      │ │  data      │
                                   └────────────┘ └────────────┘ └────────────┘
```

Full mapping in [ARCHITECTURE.md](./ARCHITECTURE.md).

## Repo layout

```
.
├── README.md                  — this file
├── ARCHITECTURE.md            — 1:1 mapping table + diagram (Mermaid + PNG)
├── SUBMISSION-PLAN.md         — H1-H10 sequencing for external reviewers
├── SCOTT-ACTION-REQUIRED.md   — maintainer-only blockers (Vertex APIs, IAM, credits)
├── SECURITY.md                — disclosure policy + IP gate
├── CODEOWNERS
├── LICENSE                    — Apache-2.0
├── adk/                       — Ceres node/state shape as ADK manifest (H5 output)
├── terraform/                 — Vertex AI Agent Builder + Memory Bank + IAM (H4 output)
├── sdk/dart-sample/           — minimal Flutter app calling hosted agent (H7 output)
└── demo/                      — recorded demo + before/after chart (H8, H10 outputs)
```

Each sub-directory has its own README describing the contents.

## Status

| Component | Status | Tracking |
|---|---|---|
| Repo created (Apache-2.0) | ✅ done | H9 ac-1 |
| IP review sign-off | ⏳ pending | H9 ac-2 |
| `make demo` end-to-end | ⏳ blocked on Vertex API enablement | H9 ac-3 |
| Architecture diagram (Mermaid + PNG) | ⏳ in progress | H9 ac-4 |
| Repo CI green | ⏳ pending | H9 ac-5 |

See [SUBMISSION-PLAN.md](./SUBMISSION-PLAN.md) for the full sequencing.

## License

Apache-2.0. See [LICENSE](./LICENSE).

## Trade-secret hygiene

This repo intentionally does **not** contain:

- Ether tier catalog, model weights, cost tables, or classifier keywords
- Pantheon system prompts beyond Ceres' node/state shape
- Per-environment Terraform state or shared-services bindings
- Customer data or production secrets

The full closed monorepo and Ether router IP remain private. Carve-out is reviewed against the IP-gate criteria in [SECURITY.md](./SECURITY.md).
