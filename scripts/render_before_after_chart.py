"""H8 — render the before/after PNG that anchors the hackathon demo video.

Consumes:
  docs/gtm/hackathon-baseline.json
    after_summary_per_intent      → per-intent p50 + token counts (live Vertex)
    methodology.human_time_per_workflow.estimates_minutes_saved_per_invocation
                                  → minutes-of-human-work avoided per call
    derived_per_intent.default_monthly_invocations_per_intent_per_tenant
                                  → multiplier convention (default 50)

Renders to:
  demo/before-after-chart.png

The chart has two panels:

  Left   — per-intent BEFORE (human-time minutes) vs AFTER (agent
           p50 latency converted to minutes). Stacked-bar style so the
           savings delta is the white space.

  Right  — projected monthly hours saved per tenant, summed across all
           6 intents at the default 50-invocations-per-intent rate.

Cost-to-serve annotations cite the gemini-2.5-flash unit prices already
in the methodology block; the demo video frame just needs the picture.

Run:
  pip install matplotlib
  python scripts/render_before_after_chart.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


HERE = Path(__file__).resolve().parent.parent
BASELINE = HERE / "docs" / "gtm" / "hackathon-baseline.json"
OUT = HERE / "demo" / "before-after-chart.png"

# Display order + nicer labels for the x-axis.
INTENT_ORDER = [
    ("check_levels", "Stock Check"),
    ("reorder_analysis", "Reorder"),
    ("demand_forecast", "Forecast"),
    ("waste_analysis", "Waste"),
    ("supplier_analysis", "Supplier"),
    ("valuation", "Valuation"),
]

# Brand palette.
COL_BEFORE = "#5B6477"   # cool slate
COL_AFTER = "#7B61FF"    # NebusAI deep-purple
COL_SAVED = "#46C58C"    # green delta accent
COL_TEXT = "#1A1F33"
COL_GRID = "#E5E7EB"


def main() -> int:
    data = json.loads(BASELINE.read_text())
    after = data["after_summary_per_intent"]
    minutes_saved = (
        data["methodology"]["human_time_per_workflow"]
        ["estimates_minutes_saved_per_invocation"]
    )
    invocations_per_month = data["derived_per_intent"][
        "default_monthly_invocations_per_intent_per_tenant"
    ]

    intents = [k for k, _ in INTENT_ORDER]
    labels = [v for _, v in INTENT_ORDER]

    # "Before" = human-time minutes per workflow (from citations).
    before_min = [minutes_saved[i] for i in intents]
    # "After" = agent p50 latency in minutes.
    after_min = [round(after[i]["p50_latency_ms"] / 1000.0 / 60.0, 3) for i in intents]
    # Delta per invocation = before - after.
    delta_min = [round(b - a, 3) for b, a in zip(before_min, after_min)]

    # Right panel = projected monthly hours saved per tenant = sum across
    # intents of (delta minutes per invocation × default monthly invocations).
    monthly_hours = round(
        sum(d * invocations_per_month for d in delta_min) / 60.0, 1
    )
    per_intent_hours = [
        round(d * invocations_per_month / 60.0, 1) for d in delta_min
    ]

    # ---- figure ---------------------------------------------------------
    fig, (ax_l, ax_r) = plt.subplots(
        1, 2,
        figsize=(13, 6),
        gridspec_kw={"width_ratios": [3, 2]},
        facecolor="white",
    )
    fig.suptitle(
        "Ceres on Vertex AI Agent Engine — before vs after",
        fontsize=16,
        fontweight="bold",
        color=COL_TEXT,
        y=0.98,
    )
    fig.text(
        0.5, 0.93,
        "Per-intent human-minutes (BEFORE) vs agent p50 latency (AFTER), and projected monthly hours saved per tenant.",
        ha="center",
        fontsize=10,
        color="#586070",
    )

    # ---- left panel: per-intent before vs after -------------------------
    x = list(range(len(intents)))
    bar_w = 0.36
    ax_l.bar([i - bar_w / 2 for i in x], before_min, bar_w,
             color=COL_BEFORE, label="Before — human-time (min/invocation)")
    ax_l.bar([i + bar_w / 2 for i in x], after_min, bar_w,
             color=COL_AFTER, label="After — agent p50 latency (min/invocation)")

    # Delta annotations on top of the before bars.
    for i, (b, d) in enumerate(zip(before_min, delta_min)):
        ax_l.text(
            i - bar_w / 2, b + max(before_min) * 0.025,
            f"−{d:.2f} min",
            ha="center",
            fontsize=8.5,
            color=COL_SAVED,
            fontweight="bold",
        )

    ax_l.set_xticks(x)
    ax_l.set_xticklabels(labels, fontsize=10, color=COL_TEXT)
    ax_l.set_ylabel("Minutes per invocation", color=COL_TEXT, fontsize=11)
    ax_l.set_title("Per-intent workflow time", fontsize=12, color=COL_TEXT, pad=12)
    ax_l.set_ylim(0, max(before_min) * 1.25)
    ax_l.yaxis.set_major_locator(plt.MultipleLocator(5))
    ax_l.grid(axis="y", linestyle="--", linewidth=0.6, color=COL_GRID)
    ax_l.set_axisbelow(True)
    for spine in ("top", "right"):
        ax_l.spines[spine].set_visible(False)
    ax_l.tick_params(colors=COL_TEXT)
    ax_l.legend(loc="upper right", framealpha=0.95, fontsize=9)

    # ---- right panel: monthly hours saved per tenant --------------------
    ax_r.barh(
        list(reversed(labels)),
        list(reversed(per_intent_hours)),
        color=COL_SAVED,
        alpha=0.9,
    )
    for i, h in enumerate(reversed(per_intent_hours)):
        ax_r.text(
            h + max(per_intent_hours) * 0.02, i,
            f"{h:.1f} h",
            va="center",
            fontsize=9.5,
            color=COL_TEXT,
        )
    ax_r.set_title(
        f"Hours saved / tenant / month\n({invocations_per_month} invocations / intent / month)",
        fontsize=12,
        color=COL_TEXT,
        pad=12,
    )
    ax_r.set_xlim(0, max(per_intent_hours) * 1.25)
    ax_r.xaxis.set_major_locator(plt.MultipleLocator(5))
    ax_r.grid(axis="x", linestyle="--", linewidth=0.6, color=COL_GRID)
    ax_r.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax_r.spines[spine].set_visible(False)
    ax_r.tick_params(colors=COL_TEXT, length=0)

    # Bottom-left: total + cost-to-serve callout.
    avg_total_tokens = sum(
        after[i]["avg_total_tokens"] for i in intents
    ) / len(intents)
    unit_in = data["methodology"]["cost_to_serve"]["unit_prices_usd"]["input_per_million_tokens"]
    unit_out = data["methodology"]["cost_to_serve"]["unit_prices_usd"]["output_per_million_tokens"]
    blended_per_call = (avg_total_tokens / 1_000_000) * ((unit_in + unit_out) / 2)
    monthly_cost = blended_per_call * invocations_per_month * len(intents)

    fig.text(
        0.5, 0.02,
        (
            f"Total: {monthly_hours:.1f} hours of human ops work removed per tenant per month  ·  "
            f"agent cost ≈ ${monthly_cost:.2f} / tenant / month "
            f"(gemini-2.5-flash, {int(avg_total_tokens):,} avg tokens × {invocations_per_month*len(intents)} calls).  "
            f"Sources: NRA / NACS / Symphony RetailAI / Bloomberg (see hackathon-baseline.json)."
        ),
        ha="center",
        fontsize=8.5,
        color="#586070",
    )

    plt.subplots_adjust(top=0.86, bottom=0.10, left=0.07, right=0.97, wspace=0.30)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT, dpi=160, facecolor="white")
    print(f"wrote {OUT}")
    print(f"summary: {monthly_hours:.1f} h/tenant/month saved · ~${monthly_cost:.2f}/tenant/month inference cost")
    return 0


if __name__ == "__main__":
    sys.exit(main())
