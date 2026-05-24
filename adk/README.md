# `adk/` — Ceres on Vertex AI Agent Engine

Python port of the Pantheon Ceres workflow, deployed to Vertex AI Agent Engine via the **Google ADK** Python SDK.

## Why Python, not YAML

The original H5 plan shipped `ceres.adk.yaml` as the manifest. While writing the deploy script we discovered the canonical Agent Engine deploy path is `vertexai.agent_engines.create(agent_engine=AdkApp(agent=python_agent))` — there is no YAML manifest deploy API. The YAML now lives at `ceres.adk.yaml.docs` as a documentation reference; the deployable is this Python package.

## Layout

```
adk/
├── agent/
│   ├── __init__.py        — exports root_agent
│   ├── ceres.py           — root + 6 sub-agents (faithful port of the LangGraph graph)
│   └── tools.py           — 8 tool functions (public-safe stubs returning canned demo data)
├── deploy.py              — idempotent deploy script (creates or updates the Agent Engine instance)
├── requirements.txt       — local-env pins
├── ceres.adk.yaml.docs    — documentation-only reference of the workflow shape
├── state-schema.json      — JSON Schema for the CeresState (still useful for docs + validators)
├── tools.yaml             — tool registry documentation
└── README.md              — this file
```

## Run it

```bash
cd adk
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python deploy.py --dry-run                # prints the plan, no Vertex calls
python deploy.py                          # creates the Agent Engine; prints resource_name
```

Prereqs (one-time; tracked in `../SCOTT-ACTION-REQUIRED.md`):

- Vertex AI + Discovery Engine APIs enabled in `olympuscloud-dev`
- ADC set up with quota project: `gcloud auth application-default set-quota-project olympuscloud-dev`
- `../terraform` applied (provides the `pantheon-agent-engine-dev` SA + Memory Bank data stores)

## The faithful-port claim

The Python `Agent` graph in `agent/ceres.py` mirrors the LangGraph workflow in the private monorepo at `backend/python/app/agents/pantheon/ceres/graph.py` one-to-one:

| LangGraph (private) | ADK (here) |
|---|---|
| `classify_intent` + `intent_router` + `analysis_router` | `root_agent`'s instruction + `sub_agents=[...]` (LLM dispatches via `transfer_to_agent`) |
| `fetch_inventory` node | `load_inventory` tool, called by each sub-agent |
| `check_levels` node | `levels_agent` + `evaluate_stock_levels` tool |
| `analyze_reorders` node | `reorders_agent` + `compute_reorder_suggestions` tool |
| `forecast_demand` node | `forecast_agent` + `forecast_demand` tool |
| `analyze_waste` node | `waste_agent` + `load_waste_data` tool |
| `analyze_suppliers` node | `suppliers_agent` + `load_supplier_data` tool |
| `calculate_valuation` node | `valuation_agent` + `compute_inventory_valuation` tool |
| `build_report` node | `root_agent`'s instruction (composes report from sub-agent output) |
| `send_alerts` node | `dispatch_alerts` tool (shared across sub-agents) |

State is held in the ADK session + Memory Bank, mirroring the `CeresState` TypedDict. Field names and types match `state-schema.json`.

## IP gate (per ../SECURITY.md)

This package is **public-safe**:
- Node graph topology + sub-agent shape: public
- Tool names + signatures + return shapes: public
- Tool implementations: **stubbed with canned demo data**. Real implementations call back into the private Olympus monorepo and are not vendored here.
- Ether tier catalog / classifier / model weights: **not present**. We hard-code `gemini-2.0-flash` so reviewers can run the demo without an Ether deployment; in production this is the Ether router endpoint.
- Prompts: describe the agent's **role** only — no Ether routing policy, no per-tenant secret context.
