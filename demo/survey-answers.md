# DevPost Submission — Survey Answer Drafts

These are the canonical answers Scott pastes into the DevPost submission form. Every claim is anchored to a checked-in artifact in this repo or its closed counterpart so the assertions are independently verifiable.

> Last refresh: post-H8 landing — drafts now reference real-Vertex evidence instead of plans.

---

## Q1 — "Which specific feature of Agent Platform was most critical to your project's impact, and what is one thing it's currently missing?"

The most critical feature was **ADK's `sub_agents` + `transfer_to_agent` transfer pattern on the managed Agent Runtime**. Our existing system — Pantheon, a graph-based orchestrator with 27 specialized agents — is already structured as a root agent that dispatches to specialists. ADK gave us a 1:1 mapping: our root `ceres` agent classifies the user's intent and transfers to one of six sub-agents (levels, reorders, forecast, waste, suppliers, valuation), each carrying its own tool set. The faithful port — visible at `adk/agent/ceres.py` and reproducible from `ARCHITECTURE.md` — lets a customer make one SDK call and get a complete agent trace from a managed Reasoning Engine with sub-second cold starts, no orchestration plumbing or container management on our side.

The one thing it's currently missing is **built-in cost-tiered model routing with per-tenant budget guardrails inside Agent Runtime**. Today you bring your own router and your own spend controls. We had to keep our internal cost-tier router (Ether) in front of Gemini so each request serves from the cheapest capable Gemini variant for that tenant's compliance tier, and so a tenant hits a hard stop before overspending. A native primitive — *"route to cheapest capable model that satisfies this tenant's tier and refuse if the call would breach a per-tenant budget"* — at the Reasoning Engine layer would let multi-tenant SaaS on Agent Platform run profitably out of the box. We measured the impact at our scale: at the demo's 300 monthly invocations per tenant the inference spend on `gemini-2.5-flash` is about $1.28/tenant/month (see `demo/before-after-chart.png` footer); without the router, mis-routing to a Claude-tier model on every call would multiply that 10–40×. The router work isn't deep — but right now every multi-tenant team building on Agent Platform writes one.

---

## Q2 — "If you could add one specific API capability or integration that would have saved you 2+ hours of work, what would it be?"

A **first-class `tenant_id` parameter on Agent Engine session and Memory Bank APIs**. Agent Memory Bank already isolates per-`user_id`, so isolation is structurally available — but the contract is implicit. We had to design and ship our own boundary discipline: encode `tenant_id` as the first segment of every `user_id` (`{tenant_id}:{user_id}`), publish a contract module (`adk/agent/tenant_user_id.py`), add a runtime guard that rejects any caller who forgets the prefix, and write a behavioral proof harness against the live engine. The end-to-end proof passes (see `demo/memory-isolation-proof.txt` — 10/10 PASS against deployed Ceres, with tenant B's session-list call confirmed empty of tenant A's session ID), but everything from the encoding to the failure-injection test was infrastructure we had to build because the substrate doesn't enforce tenant isolation natively.

If `agent_engines.AdkApp.create_session(tenant_id=…, user_id=…)` and `agent_engine.async_search_memory(tenant_id=…, …)` accepted tenant_id directly — and the API rejected cross-tenant reads at the substrate boundary the way it does for user_id today — every multi-tenant team would skip the boundary work we did. Conservatively, the contract + tests + proof took us a day; a built-in `tenant_id` parameter would have removed all of it. The same pattern applies to **budget-and-tier routing**: a `route_to_cheapest_capable_model(tenant_id, tier)` primitive at the same layer would close the gap from Q1 with one API call.

---

## Evidence map (so the answers are verifiable)

| Claim | Where to verify |
|---|---|
| Pantheon graph 1:1 to ADK | `adk/agent/ceres.py` · `ARCHITECTURE.md` mapping table |
| Sub-second cold starts on Reasoning Engine | Cloud Logging on the deployed engine in `olympuscloud-dev` |
| Tenant_id encoded in user_id + runtime guard | `adk/agent/tenant_user_id.py` + 14 unit tests in `adk/test_tenant_user_id.py` |
| Tenant B cannot see tenant A's sessions (live) | `demo/memory-isolation-proof.txt` — 10/10 PASS |
| One SDK call from customer app | `sdk/dart-sample/lib/main.dart` calls `olympus_sdk.agent.callVertexAgent('ceres', ...)` |
| Per-intent live measurements | `docs/gtm/hackathon-baseline-after.json` — 18 live captures across 6 intents |
| $1.28/tenant/month inference cost | `docs/gtm/hackathon-baseline.json` methodology.cost_to_serve block |
| 112 hours human ops work removed | `docs/gtm/hackathon-baseline.json` methodology.human_time_per_workflow citations (NRA, NACS, Symphony RetailAI, Bloomberg) |
| Ether kept in front of Gemini for cost routing | This repo intentionally does not vendor the Ether router (IP gate per `SECURITY.md`); the survey answer describes its role only |

---

## What these answers intentionally do NOT claim

- We do NOT claim Agent Platform features we didn't actually exercise (e.g. A2A protocol, Reasoning Engine fine-tuning).
- We do NOT claim cross-region / DR — the engine runs in a single region (`us-central1`).
- We do NOT name Ether's tier catalog, weights, or classifier rules. Per `SECURITY.md` these are trade secret.
- We do NOT cite real tenant data or customer names. The proof tenants are `demo-tenant-a` / `demo-tenant-b`.
