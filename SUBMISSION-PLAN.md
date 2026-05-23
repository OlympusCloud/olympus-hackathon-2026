# Submission Plan

Tracking the 10 hackathon work items (`H1`–`H10`) from epic [#4797](https://github.com/OlympusCloud/olympus-cloud-gcp/issues/4797) in the private monorepo. This document is the public-friendly summary; the per-item acceptance criteria live in the closed issues.

## Sequencing

```
H1 ────┐
       ▼
H2 ──▶ H3 ──▶ H4 ──▶ H5 ──▶ H6 ──▶ H7 ──▶ H8 ──▶ H9 ──▶ H10
       │                                                    ▲
       └────────────────────────────────────────────────────┘
            (H3 substrate work can land in parallel)
```

| # | Title | Status | Output goes to |
|---|---|---|---|
| H1 | Confirm rules + provision Vertex AI access (dev) | 🟡 partial | maintainer-only |
| H2 | Lock Ceres baseline metric (before-state) | ⬜ pending | `demo/before-after-chart.png` |
| H3 | Add `VERTEX_AGENT_ENGINE` substrate (base + runtime + selector) | 🟢 PR open | private monorepo |
| H4 | Terraform: Vertex AI Agent Builder + Memory Bank + IAM (dev) | ⬜ pending | [`terraform/`](./terraform/) |
| H5 | Port Ceres LangGraph → ADK manifest, deploy on Agent Runtime | ⬜ pending | [`adk/`](./adk/) |
| H6 | Wire Agent Memory Bank with tenant-scoped isolation | ⬜ pending | private monorepo + demo evidence |
| H7 | Expose hosted Ceres via `olympus_sdk` (gateway route + Dart SDK) | ⬜ pending | [`sdk/dart-sample/`](./sdk/dart-sample/) |
| H8 | Instrument before/after metric + ClickHouse dashboard for demo | ⬜ pending | `demo/before-after-chart.png` |
| H9 | Create + populate public carve-out repo (this one) | 🟡 in progress | this repo |
| H10 | Record demo video + finalize survey answers + submit | ⬜ blocked on H6, H8 | DevPost |

## Critical path

1. **This week (Days 1–7)** — H1 blockers cleared (Vertex APIs enabled, IAM, credits, rules), H3 + H4 land, ADK port (H5) starts.
2. **Next week (Days 8–14)** — H5 + H6 ship: Ceres running on Vertex Agent Runtime with tenant-scoped Memory Bank. H7 wires the SDK.
3. **Final week (~June 5 deadline)** — H8 chart, H9 carve-out CI green, H10 video + submission.

## Acceptance gate (H9 ac-3): `make demo` from a clean machine

When complete, a reviewer can run:

```bash
git clone https://github.com/OlympusCloud/olympus-hackathon-2026
cd olympus-hackathon-2026
make demo
```

…and see Ceres respond with a real `Report` from a real Vertex AI Agent Runtime deployment. Setup steps and credential requirements are in [`demo/README.md`](./demo/README.md).

## Honest survey answer principle

We will only claim ADK / Agent Runtime / Memory Bank features we **actually exercised** in this submission. Draft answers live in `docs/gtm/GOOGLE-HACKATHON-PLAN.md` (private repo) until H10 finalizes them.

## Trade-secret hygiene

Every file added to this repo is reviewed against the IP-gate in [SECURITY.md](./SECURITY.md) — Ether tier catalog, model weights, classifier internals, and prompt IP for the other 26 Pantheon agents stay private.
