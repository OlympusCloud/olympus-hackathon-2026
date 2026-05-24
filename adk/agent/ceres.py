"""Ceres agent — Python ADK port of the LangGraph workflow.

Faithful 1:1 to backend/python/app/agents/pantheon/ceres/graph.py (private
monorepo). The structure is:

  root_agent (classify_intent + orchestration)
   ├─ levels_agent          → check_levels tool
   ├─ reorders_agent        → compute_reorder_suggestions tool
   ├─ forecast_agent        → forecast_demand tool
   ├─ waste_agent           → load_waste_data tool
   ├─ suppliers_agent       → load_supplier_data tool
   └─ valuation_agent       → compute_inventory_valuation tool

  All sub-agents share the load_inventory + dispatch_alerts tools and the
  build_report responsibility (the root_agent composes the final report
  from sub-agent outputs after dispatch via transfer_to_agent).

  Memory: tenant-scoped via Agent Memory Bank (wired at deploy time).
  Inference: routed through Olympus Ether in production; here we use
  gemini-2.0-flash directly so the public carve-out has no Ether wiring.
"""

from __future__ import annotations

from google.adk.agents import Agent

from .tools import (
    compute_inventory_valuation,
    compute_reorder_suggestions,
    dispatch_alerts,
    evaluate_stock_levels,
    forecast_demand,
    load_inventory,
    load_supplier_data,
    load_waste_data,
)

# A single model variant for the public carve-out. In production this is
# the Olympus Ether router endpoint, which selects the cheapest capable
# Gemini variant per request + per-tenant budget. The router is private.
MODEL = "gemini-2.0-flash"

# ---------------------------------------------------------------------------
# Sub-agents — one per analytical intent. Each one carries the inventory
# loader + its specific analysis tool. The dispatch_alerts tool is shared
# so any sub-agent can fire alerts when its analysis surfaces a problem.
# ---------------------------------------------------------------------------

levels_agent = Agent(
    model=MODEL,
    name="levels_agent",
    description=(
        "Classifies inventory items as critical, low, normal, or overstocked "
        "against the configured thresholds. Surfaces a stock_alerts list."
    ),
    instruction=(
        "Use load_inventory then evaluate_stock_levels. Return the list of "
        "alerts with the SKU, current quantity, par level, and status. "
        "Be concise."
    ),
    tools=[load_inventory, evaluate_stock_levels, dispatch_alerts],
)

reorders_agent = Agent(
    model=MODEL,
    name="reorders_agent",
    description="Suggests reorder quantities for items at or below reorder point.",
    instruction=(
        "Use load_inventory then compute_reorder_suggestions. Return the "
        "list of suggestions with SKU, suggested quantity, and estimated "
        "cost. Total the cost at the end."
    ),
    tools=[load_inventory, compute_reorder_suggestions, dispatch_alerts],
)

forecast_agent = Agent(
    model=MODEL,
    name="forecast_agent",
    description="Per-SKU demand forecasts over a 14-day horizon by default.",
    instruction=(
        "Use load_inventory then forecast_demand. Return per-SKU expected "
        "total demand with lower/upper bounds and confidence."
    ),
    tools=[load_inventory, forecast_demand, dispatch_alerts],
)

waste_agent = Agent(
    model=MODEL,
    name="waste_agent",
    description="Last-30-day shrink / waste / expiry analysis.",
    instruction=(
        "Use load_waste_data. Report total waste cost, waste rate, and the "
        "top waste SKU. Flag if waste rate exceeds 5%."
    ),
    tools=[load_waste_data, dispatch_alerts],
)

suppliers_agent = Agent(
    model=MODEL,
    name="suppliers_agent",
    description="Supplier reliability scorecard.",
    instruction=(
        "Use load_supplier_data. Surface suppliers below the 0.80 "
        "reliability threshold and explain why (on-time, fill rate, defect)."
    ),
    tools=[load_supplier_data, dispatch_alerts],
)

valuation_agent = Agent(
    model=MODEL,
    name="valuation_agent",
    description="Total inventory valuation at cost, broken down by category.",
    instruction=(
        "Use load_inventory then compute_inventory_valuation. Return the "
        "total dollar valuation plus the per-category breakdown."
    ),
    tools=[load_inventory, compute_inventory_valuation],
)


# ---------------------------------------------------------------------------
# Root agent — classifies intent + transfers to the appropriate sub-agent.
# This is the entry point AdkApp invokes. The sub_agents wiring lets the
# LLM call transfer_to_agent(name=...) to dispatch (the ADK equivalent of
# the LangGraph intent_router + analysis_router).
# ---------------------------------------------------------------------------

ROOT_INSTRUCTION = """You are Ceres, the Pantheon inventory & supply-chain
agent. Read the user's query and classify it into one of these intents:

  - check_levels       → transfer to levels_agent
  - reorder_analysis   → transfer to reorders_agent
  - demand_forecast    → transfer to forecast_agent
  - waste_analysis     → transfer to waste_agent
  - supplier_analysis  → transfer to suppliers_agent
  - valuation          → transfer to valuation_agent
  - generate_report    → transfer to levels_agent (full sweep starting point)
  - other              → answer the query directly using the inventory
                         context if available; do not transfer

After a sub-agent returns its analysis, compose a structured report:
- top-line summary (1-2 sentences)
- the relevant findings as a bulleted list
- a recommendations list (what should the operator do next?)

If the analysis surfaced items needing immediate attention, include
them as a clear ACTION REQUIRED block at the top of the response.

Always be specific about SKUs and quantities. Never invent inventory
data — use only what tools return."""

root_agent = Agent(
    model=MODEL,
    name="ceres",
    description=(
        "Pantheon Ceres — inventory & supply-chain agent. Classifies "
        "requests and dispatches to one of six analysis sub-agents, then "
        "composes a structured report."
    ),
    instruction=ROOT_INSTRUCTION,
    sub_agents=[
        levels_agent,
        reorders_agent,
        forecast_agent,
        waste_agent,
        suppliers_agent,
        valuation_agent,
    ],
)
