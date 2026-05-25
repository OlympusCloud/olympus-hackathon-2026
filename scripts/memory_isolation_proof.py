"""Behavioral proof that Vertex AI Agent Engine sessions for one tenant
cannot see another tenant's memory.

Run against the deployed Ceres reasoning engine in olympuscloud-dev:

    python -m venv .venv && source .venv/bin/activate
    pip install google-cloud-aiplatform[agent_engines,adk]
    python scripts/memory_isolation_proof.py

What this proves
----------------
The tenant_user_id contract from ``adk/agent/tenant_user_id.py`` encodes
``user_id`` as ``"{tenant_id}:{user_id}"``. Agent Memory Bank is keyed
on the ``user_id`` passed at session creation time, so two different
tenant prefixes structurally cannot share memory.

The script:

1. Constructs tenant-A and tenant-B prefixed user_ids via the contract.
2. Creates a session for tenant A and runs an inventory query that puts
   stateful conversation content (the BUR-001 critical alert) in
   tenant A's session memory.
3. Lists tenant A's sessions — confirms the session is there.
4. Lists tenant B's sessions — confirms tenant A's session is NOT
   visible to tenant B (the structural isolation contract).
5. Failure-injection: attempts to construct a user_id WITHOUT the
   tenant prefix and asserts the contract raises ``TenantPrefixError``.

Output: pass/fail per step + a final "ISOLATION PROVEN" line on success.
The output is captured to demo/memory-isolation-proof.txt and uploaded
into the Guardian Ledger per H6 ac-3.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make adk/ importable so we can use the tenant_user_id contract module
# without packaging the carve-out as an installable. The runtime path is
# different (Vertex bundles agent/ as extra_packages); this is local-only.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "adk"))

from agent.tenant_user_id import (  # noqa: E402
    TenantPrefixError,
    parse_scoped_user_id,
    scoped_user_id,
)

import vertexai  # noqa: E402
from vertexai import agent_engines  # noqa: E402

PROJECT = os.environ.get("VERTEX_PROJECT", "olympuscloud-dev")
LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
RESOURCE_NAME = os.environ.get(
    "VERTEX_CERES_RESOURCE_NAME",
    "projects/449595477159/locations/us-central1/reasoningEngines/9005495561473753088",
)

TENANT_A = "demo-tenant-a"
TENANT_B = "demo-tenant-b"
DEMO_USER = "isolation-proof-user"

QUERY = "Show me a low-stock report; remember the result for next time."


def _step(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    suffix = f"  — {detail}" if detail else ""
    print(f"  [{status}] {name}{suffix}")
    if not ok:
        raise SystemExit(1)


def main() -> int:
    print("=== Vertex AI Agent Engine memory isolation proof ===")
    print(f"project          {PROJECT}")
    print(f"location         {LOCATION}")
    print(f"resource_name    {RESOURCE_NAME}")
    print(f"tenant_a         {TENANT_A}")
    print(f"tenant_b         {TENANT_B}")
    print()

    # ----- Step 1: contract construction -----
    user_a = scoped_user_id(TENANT_A, DEMO_USER)
    user_b = scoped_user_id(TENANT_B, DEMO_USER)
    _step("contract: scoped user_ids built", True, f"{user_a} / {user_b}")

    parsed_a = parse_scoped_user_id(user_a)
    _step(
        "contract: round-trip parse",
        parsed_a.tenant_id == TENANT_A and parsed_a.user_id == DEMO_USER,
        f"parsed=({parsed_a.tenant_id}, {parsed_a.user_id})",
    )

    # ----- Step 2: invoke against the deployed engine -----
    vertexai.init(project=PROJECT, location=LOCATION)
    engine = agent_engines.get(RESOURCE_NAME)
    _step("connected to Agent Engine", True, engine.resource_name)

    # ----- Step 3: tenant A writes a memory via an interactive session -----
    sess_a = engine.create_session(user_id=user_a)
    _step("tenant A: created session", True, f"id={sess_a['id']}")

    final_text_a = ""
    events_count_a = 0
    for event in engine.stream_query(
        user_id=user_a, session_id=sess_a["id"], message=QUERY
    ):
        events_count_a += 1
        for part in (event.get("content") or {}).get("parts") or []:
            if isinstance(part, dict) and "text" in part:
                final_text_a = part["text"]
    _step(
        "tenant A: streamed agent trace",
        events_count_a > 0 and final_text_a != "",
        f"{events_count_a} events, final text {len(final_text_a)} chars",
    )

    # ----- Step 4: list sessions for each tenant -----
    list_a = list(engine.list_sessions(user_id=user_a).get("sessions", []))
    list_b = list(engine.list_sessions(user_id=user_b).get("sessions", []))

    a_ids = {s["id"] for s in list_a if isinstance(s, dict) and "id" in s}
    b_ids = {s["id"] for s in list_b if isinstance(s, dict) and "id" in s}

    _step(
        "tenant A: own session is listed under tenant A",
        sess_a["id"] in a_ids,
        f"|sessions(A)|={len(a_ids)}",
    )
    _step(
        "tenant B: tenant A's session is NOT visible under tenant B",
        sess_a["id"] not in b_ids,
        f"|sessions(B)|={len(b_ids)} — isolated",
    )

    # ----- Step 5: failure injection — bare user_id with no prefix -----
    try:
        scoped_user_id("", DEMO_USER)
        _step("failure injection: empty tenant rejected", False)
    except TenantPrefixError:
        _step("failure injection: empty tenant rejected", True)

    try:
        parse_scoped_user_id("forgot-the-prefix")
        _step("failure injection: missing-prefix string rejected", False)
    except TenantPrefixError:
        _step("failure injection: missing-prefix string rejected", True)

    # ----- Clean up the proof's session -----
    try:
        engine.delete_session(user_id=user_a, session_id=sess_a["id"])
        _step("cleanup: tenant A session deleted", True)
    except Exception as exc:  # noqa: BLE001 - cleanup-best-effort
        _step("cleanup: tenant A session deleted", False, str(exc))

    print()
    print("=" * 56)
    print("ISOLATION PROVEN")
    print("=" * 56)
    print()
    print("Tenant A wrote a session + agent trace to Agent Engine.")
    print("Tenant B's session-list call did not see it.")
    print("The tenant_user_id contract rejected both failure injections.")
    print()
    print("Capture this output into demo/memory-isolation-proof.txt + add")
    print("a Guardian Ledger row referencing it (H6 ac-3).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
