"""Ceres agent package — Python ADK port of the Pantheon Ceres workflow.

The shape mirrors the private monorepo at
backend/python/app/agents/pantheon/ceres/ one-to-one:

  classify_intent --(intent_router)--> fetch_inventory --(analysis_router)--> 6 analysis nodes
                                            \\                                       \\
                                             ----> handle_query ----.                 \\
                                                                     \\                 \\
                                                                      ---> build_report -> send_alerts -> END

The translation lives in `ceres.py` (root_agent + sub_agents). Tool function
stubs are in `tools.py` — real implementations stay in the private monorepo
per the IP gate in ../SECURITY.md; the public package returns canned demo
data so the end-to-end flow runs without leaking private logic.
"""

# Lazy re-export: only resolve `root_agent` on first access. Importing
# `root_agent` eagerly pulls in `google.adk.agents`, which deploy.py and
# the runtime have available but unit tests for tenant_user_id et al.
# (which only need the validation helpers) do not.
__all__ = ["root_agent"]


def __getattr__(name):  # PEP 562
    if name == "root_agent":
        from .ceres import root_agent as _ra

        return _ra
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
