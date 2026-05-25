# Demo Script — Ceres on Vertex AI Agent Engine (Hackathon 2026)

**Target length**: 3:00 (hard cap 3:30 — DevPost guidance).
**Submitter**: Scott Houghton / NebusAI.
**Last rehearsal**: TBD — record once Scott has 30 min uninterrupted.

This script is the canonical narrative the judges will see. Every claim in it is backed by a checked-in artifact (chart, proof log, trace, PR link) — see the **Evidence column** on every beat.

---

## Tooling for recording

- **Screen capture**: Loom or QuickTime, 1080p, system audio on
- **Camera-in-frame**: optional 150×150 picture-in-picture; keeps it human
- **Browser tabs needed** (open in this order):
  1. `https://github.com/OlympusCloud/olympus-hackathon-2026` — public carve-out
  2. `demo/before-after-chart.png` (rendered in GitHub's image viewer or as a desktop window)
  3. `demo/memory-isolation-proof.txt` (raw text — for the isolation beat)
  4. A terminal already in `olympus-hackathon-2026/` with the venv active and `gcloud auth application-default print-access-token` healthy
  5. Vertex AI Agent Engine console: `https://console.cloud.google.com/vertex-ai/reasoning-engines?project=olympuscloud-dev`
- **Pre-recorded fallback**: if the live call goes long, cut to a 15-second pre-rendered call trace clip from a dry run

---

## Beat-by-beat (3:00)

| Time | Beat | What you say | What's on screen | Evidence |
|---|---|---|---|---|
| **0:00 – 0:15** | **Opener** | "I'm Scott Houghton from NebusAI. We're an AI-native PaaS — independent operators build their business OS on our platform and it's run by AI agents. For this hackathon, I took one of our Pantheon agents — Ceres, our inventory and supply-chain agent — and ported it to Google's Agent Platform end-to-end. Let me show you what that means." | Title card: "Ceres on Vertex AI Agent Engine — NebusAI." Sub: "1 Pantheon agent · 6 inventory intents · per-tenant memory · 1 SDK call from a customer app." | — |
| **0:15 – 0:45** | **The architecture mapping (the 1:1 port)** | "Pantheon is our graph-based multi-agent runtime. It already runs on Cloud Run, Cloud Functions, CF Workers, and CF Containers. We added Vertex AI Agent Engine as the fourth substrate — ADK preserved the graph topology, Agent Memory Bank gave us tenant isolation as a substrate primitive, and inference still routes through our internal Ether cost-tier router so Gemini-2.5-flash serves the cheap T1/T2 calls and Claude serves the expensive T4/T6 ones." | Show `ARCHITECTURE.md` mapping table side-by-side with the `agent/ceres.py` ADK code. Highlight the `root_agent` + 6 `sub_agents` matching the LangGraph nodes 1:1. | `adk/agent/ceres.py` · `ARCHITECTURE.md` · PR #5 (Python ADK port) |
| **0:45 – 1:30** | **Live agent call from a customer app** | "Here's what a customer app actually does. One SDK method call — `olympus_sdk.agent.callVertexAgent('ceres', 'low stock report')`. The Olympus gateway proxies to Vertex Agent Engine. The agent classifies the intent, transfers to the levels sub-agent, calls the inventory tool, evaluates against the par-level thresholds, composes a structured response, streams it back. Watch." | Run the headless smoke from the terminal: `HEADLESS=1 dart run sdk/dart-sample/lib/main.dart`. Show the event trace streaming (root → transfer_to_agent → load_inventory → evaluate_stock_levels → composed report) on screen, then the final composed text. | Live trace · PR #4 (Dart sample) · PR #4957 (gateway leg) · `olympus-sdk-dart#144` (SDK method) |
| **1:30 – 2:05** | **The tenant-isolation primitive** | "Multi-tenant SaaS hinges on isolation. Agent Memory Bank gives us a substrate-native isolation primitive — keyed per user_id, sessions for one tenant cannot read another's memory. We push tenant_id into the first segment of user_id at the boundary, with a runtime guard that rejects any call site that forgets the prefix. This is the live proof I ran against the deployed engine yesterday." | Open `demo/memory-isolation-proof.txt`. Scroll through the 10 PASS lines — `tenant A: streamed agent trace`, then `tenant B: tenant A's session is NOT visible under tenant B`, then `failure injection: missing-prefix string rejected`. End on **ISOLATION PROVEN**. | `demo/memory-isolation-proof.txt` · PR #8 (H6 — memory isolation) |
| **2:05 – 2:40** | **The before/after chart — why this matters** | "On the impact side: a tenant on Ceres recovers 112 hours of human operations work per month — that's two and a half weeks of full-time staff time, removed by one agent. The agent itself costs about a dollar twenty-eight per tenant per month at Gemini-2.5-flash rates. That's eighty-eight times return on inference spend. Sources are NRA, NACS, Symphony RetailAI, Bloomberg — all cited in the baseline JSON." | Pop `demo/before-after-chart.png` full-screen. Trace the bars left panel (per-intent before vs after), then right panel (hours saved per tenant per month), then read the footer line. | `demo/before-after-chart.png` · `docs/gtm/hackathon-baseline.json` · PR #10 (H8 — chart) |
| **2:40 – 3:00** | **Close** | "Everything I showed today is reproducible from the public carve-out repo — Apache-2.0, the ADK Python source, the Terraform, the Dart sample, the proof script. A small team — me, a few agents — shipped a production-grade port to Google's Agent Platform in two weeks. Thanks for watching. Repo link is on the submission page." | Title card: repo URL + Apache-2.0 badge + "OlympusCloud/olympus-hackathon-2026". | Carve-out repo URL |

**Total**: 3:00 hard. If the live call runs long, cut to the pre-rendered clip noted in the tooling section.

---

## Rehearsal checklist (pre-record)

- [ ] Mic check — speak ten seconds, listen back, adjust input gain
- [ ] Vertex AI Agent Engine instance is up — `vertexai.agent_engines.get(...)` from the venv returns the resource without 404
- [ ] Demo tenant JWT is fresh — `gcloud secrets versions access` returns a non-empty token
- [ ] `HEADLESS=1 dart run sdk/dart-sample/lib/main.dart` returns a non-empty Ceres `Report` on a dry run
- [ ] `demo/memory-isolation-proof.txt` is the latest captured-stdout (re-run `scripts/memory_isolation_proof.py` if it's older than 7 days)
- [ ] `demo/before-after-chart.png` opens at full quality (not the GitHub-thumbnailed version)
- [ ] All open browser tabs are loaded and signed-in
- [ ] Notifications silenced (macOS Do Not Disturb on)
- [ ] Screen resolution matches recording target (1920×1080 native, no scaling)

---

## Post-record

1. Upload to unlisted YouTube (NOT public — DevPost embeds + judges-only is the right access pattern).
2. Capture the YouTube URL.
3. Paste into `OlympusCloud/olympus-cloud-gcp#4807` (H10 ac-1) AND the DevPost submission form.
4. Finalize the survey answer drafts in `docs/gtm/GOOGLE-HACKATHON-PLAN.md` §6 — make sure every claim in the answer is also visible in the video.
5. Submit via DevPost.
6. Drop a comment on H10 + the parent epic #4797 with the submission URL.

---

## Fail-safes

| Failure mode | Mitigation |
|---|---|
| Live agent call returns a 5xx mid-record | Stop recording, restart the agent engine, retry. The script's <30s headless run is short enough to redo. |
| Agent returns a weird response (LLM non-determinism) | Re-run with a different demo query. The 6 intents have prompts in `scripts/baseline_capture.py:INTENT_PROMPTS`; any of them work. |
| Memory isolation proof somehow fails mid-record | Use the captured `demo/memory-isolation-proof.txt` instead; cut the live re-run. |
| You stumble on the architecture-mapping beat | The mapping table in `ARCHITECTURE.md` is the script — read directly off it. |
| Recording runs >3:30 | DevPost soft-caps at 3:00; ~3:30 is the hard cap most judges still watch. Cut the longest beat (usually the architecture explanation) — open with the live call instead. |

---

## What this script intentionally does NOT say

- We do NOT name the Ether tier catalog, weights, or classifier rules. The script says "routes through our internal Ether cost-tier router" once and moves on.
- We do NOT name competitor agents. The narrative is about what's possible on Google's stack, not about beating someone else.
- We do NOT promise availability or pricing. The hackathon submission is a technical demo, not a marketing landing page.
- We do NOT cite live customer data or tenants. The "demo-tenant-a" / "demo-tenant-b" pair is what the script + proof use.
