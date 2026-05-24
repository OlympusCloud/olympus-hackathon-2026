# `adk/` — Ceres ADK manifest

Output of hackathon work item **H5** (port Ceres LangGraph → ADK manifest, deploy on Agent Runtime).

## What lands here

- `ceres.adk.yaml` (or `.json`) — ADK manifest preserving Ceres' 11-node graph from the LangGraph source.
- `state-schema.json` — the TypedDict state translated to ADK session state schema.
- `tools.yaml` — tool name registry (names only; implementations stay in the private monorepo).
- `prompts/` — node-level system prompts (Ceres-only; other Pantheon agent prompts are not public-safe).
- `deploy.sh` — wrapper around `gcloud ai reasoning-engines deploy` that points at the manifest + service account from [`../terraform/`](../terraform/).

## Source of truth

The LangGraph version lives in the private monorepo at `backend/python/app/agents/pantheon/ceres/`. The mapping is documented in [`../ARCHITECTURE.md`](../ARCHITECTURE.md#ceres-workflow-what-we-ported).

## Status

⬜ Pending — waiting on H1 (Vertex API enablement) and H4 (Terraform) to land.

## How to verify the port is faithful

Read `graph.py` + `state.py` from the private monorepo side-by-side with `ceres.adk.yaml`. Every node, every conditional edge, every TypedDict field must have a 1:1 correspondence. The behavior must be identical — we are changing **runtime substrate**, not workflow logic.
