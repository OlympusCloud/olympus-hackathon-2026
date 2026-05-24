# `demo/` — 3-minute demo + before/after chart

Outputs of hackathon work items **H8** (before/after metric) and **H10** (demo video + submission).

## What lands here

- `demo-script.md` — the 3-minute narrative beat-by-beat (customer app → SDK call → Pantheon-on-Vertex → Gemini via Ether → Memory Bank tenant isolation → HITL approval → action taken).
- `before-after-chart.png` — rendered chart from H8: human ops hours removed for one Ceres workflow + cost-to-serve breakdown showing Ether's Gemini tier routing.
- `architecture-diagram.png` — rendered version of the mapping in [`../ARCHITECTURE.md`](../ARCHITECTURE.md).
- `demo-video.md` — link to the unlisted demo video (uploaded at H10 submission time).
- `Makefile` (or top-level) — `make demo` target that bootstraps the Dart sample, makes the live call, and prints the resulting Ceres `Report` to stdout. Satisfies H9 ac-3.

## How `make demo` works (target shape)

```
make demo
├── check Vertex AI agent endpoint reachable (from terraform output)
├── flutter pub get in sdk/dart-sample
├── run a headless dart script that:
│   ├── authenticates against the Olympus gateway with a demo tenant JWT
│   ├── invokes olympusSdk.ai.runAgent('ceres', query='low-stock report')
│   └── prints the returned Report JSON
└── exit 0 on a non-empty Report
```

The credential bundle (gateway URL + demo tenant JWT + agent endpoint) is loaded from environment variables; defaults are documented in `demo-script.md`. Reviewers without these credentials can still watch the recorded video and read the script.

## Status

⬜ Pending — waiting on H5 + H6 + H7 + H8.
