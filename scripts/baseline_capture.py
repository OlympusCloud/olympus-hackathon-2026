"""Capture per-intent baseline metrics by running the deployed Ceres
agent through all 6 analysis intents.

H2 — populates the "after" side of the before/after comparison that
H8's ClickHouse dashboard renders. The "before" side comes from
ClickHouse's ``pantheon_agent_runs`` rows for the pre-port Cloud-Run
Ceres deployment; the query template is in
``docs/gtm/hackathon-baseline.json`` under ``methodology.before_query``.

Run:

    source .venv/bin/activate
    pip install "google-cloud-aiplatform[agent_engines,adk]"
    python scripts/baseline_capture.py
        --out=docs/gtm/hackathon-baseline-after.json

Each intent is exercised with a representative prompt + the streamed
event trace is consumed; we record per-call latency, event count,
and prompt + candidate + thoughts + total token counts (from Vertex
``usage_metadata``). The script aggregates p50 / p95 across N runs
per intent (default N=3) so the numbers don't hinge on a single call.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "adk"))

from agent.tenant_user_id import scoped_user_id  # noqa: E402

import vertexai  # noqa: E402
from vertexai import agent_engines  # noqa: E402

PROJECT = os.environ.get("VERTEX_PROJECT", "olympuscloud-dev")
LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
RESOURCE_NAME = os.environ.get(
    "VERTEX_CERES_RESOURCE_NAME",
    "projects/449595477159/locations/us-central1/reasoningEngines/9005495561473753088",
)
TENANT = "demo-tenant-a"
USER = "baseline-capture-user"

# One representative prompt per CeresIntent. The intent name on the left
# matches CeresIntent in state-schema.json so the JSON output is the same
# shape the H8 chart consumes.
INTENT_PROMPTS = {
    "check_levels": "Show me a low-stock report.",
    "reorder_analysis": "What should I reorder right now?",
    "demand_forecast": "Forecast demand for the next 14 days.",
    "waste_analysis": "Show me my waste over the last 30 days.",
    "supplier_analysis": "Which of my suppliers are underperforming?",
    "valuation": "What's my current inventory valuation?",
}


def _run_once(engine: Any, prompt: str) -> dict[str, Any]:
    """Run one prompt against the agent; return latency + token counts."""
    user_id = scoped_user_id(TENANT, USER)
    session = engine.create_session(user_id=user_id)
    session_id = session["id"]

    started = time.perf_counter()
    prompt_tokens = candidate_tokens = thoughts_tokens = total_tokens = 0
    events_count = 0
    final_text_chars = 0

    try:
        for event in engine.stream_query(
            user_id=user_id, session_id=session_id, message=prompt
        ):
            events_count += 1
            usage = event.get("usage_metadata") or {}
            prompt_tokens += int(usage.get("prompt_token_count") or 0)
            candidate_tokens += int(usage.get("candidates_token_count") or 0)
            thoughts_tokens += int(usage.get("thoughts_token_count") or 0)
            total_tokens += int(usage.get("total_token_count") or 0)
            for part in (event.get("content") or {}).get("parts") or []:
                if isinstance(part, dict) and "text" in part:
                    final_text_chars = len(part["text"])
    finally:
        try:
            engine.delete_session(user_id=user_id, session_id=session_id)
        except Exception:  # noqa: BLE001 - best-effort cleanup
            pass

    return {
        "latency_ms": round((time.perf_counter() - started) * 1000.0, 1),
        "events_count": events_count,
        "prompt_tokens": prompt_tokens,
        "candidates_tokens": candidate_tokens,
        "thoughts_tokens": thoughts_tokens,
        "total_tokens": total_tokens,
        "final_text_chars": final_text_chars,
    }


def _aggregate(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-intent runs into a baseline summary row."""
    latencies = [r["latency_ms"] for r in runs]
    totals = [r["total_tokens"] for r in runs]
    return {
        "runs": len(runs),
        "p50_latency_ms": round(statistics.median(latencies), 1),
        "p95_latency_ms": round(
            statistics.quantiles(latencies, n=20)[-1] if len(latencies) >= 2 else latencies[0],
            1,
        ),
        "avg_total_tokens": round(statistics.mean(totals), 1),
        "avg_events_count": round(
            statistics.mean(r["events_count"] for r in runs), 1
        ),
        "raw_runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="docs/gtm/hackathon-baseline-after.json",
        help="Output path (default writes into the carve-out's docs/gtm/).",
    )
    parser.add_argument(
        "--runs-per-intent",
        type=int,
        default=3,
        help="How many times to invoke each intent (default 3).",
    )
    args = parser.parse_args()

    print(f"project        {PROJECT}")
    print(f"location       {LOCATION}")
    print(f"resource_name  {RESOURCE_NAME}")
    print(f"tenant         {TENANT}")
    print(f"runs/intent    {args.runs_per_intent}")
    print()

    vertexai.init(project=PROJECT, location=LOCATION)
    engine = agent_engines.get(RESOURCE_NAME)

    per_intent: dict[str, dict[str, Any]] = {}
    for intent, prompt in INTENT_PROMPTS.items():
        print(f"-- {intent}: {prompt}")
        runs = []
        for i in range(args.runs_per_intent):
            row = _run_once(engine, prompt)
            print(
                f"   run {i + 1}: {row['latency_ms']:>7.1f}ms  "
                f"{row['events_count']:>2} events  "
                f"{row['total_tokens']:>5} tokens"
            )
            runs.append(row)
        per_intent[intent] = _aggregate(runs)
        print()

    payload = {
        "_meta": {
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "resource_name": RESOURCE_NAME,
            "model": "gemini-2.5-flash",
            "tenant_id": TENANT,
            "runs_per_intent": args.runs_per_intent,
            "substrate": "vertex-agent-engine",
            "ip_safe": True,
            "purpose": (
                "AFTER-side baseline for H2/H8. The BEFORE-side baseline "
                "comes from pantheon_agent_runs ClickHouse rows for the "
                "Cloud-Run Ceres deployment (see hackathon-baseline.json "
                "for the query template)."
            ),
        },
        "per_intent": per_intent,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out} ({len(per_intent)} intents)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
