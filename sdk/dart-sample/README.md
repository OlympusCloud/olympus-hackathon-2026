# `sdk/dart-sample/` — minimal Flutter app calling hosted Ceres

Output of hackathon work item **H7**. Calls the deployed Ceres agent through `olympus_sdk` and prints the report.

## Two modes

| Mode | Command | Use |
|---|---|---|
| UI | `flutter run -d chrome` | Live demo; type a query, get a Ceres report |
| Headless | `HEADLESS=1 dart run lib/main.dart` | Single round-trip → stdout. The `make demo` path. |

## Setup

```bash
cd sdk/dart-sample
flutter pub get
cp lib/demo_credentials.dart.example lib/demo_credentials.dart
# edit demo_credentials.dart with the values from terraform output + a demo tenant JWT
```

`demo_credentials.dart` is gitignored — never commit real values.

## What it does

1. Constructs an `OlympusClient` against the gateway in `demo_credentials.dart`.
2. Calls `client.agent.callVertexAgent(agentName: 'ceres', ...)` — the SDK method added in `olympus-sdk-dart#144`. The gateway forwards the call to `POST /api/v1/agent/vertex/ceres` (private-monorepo route `olympus-cloud-gcp#4957`), which streams the agent trace from Vertex AI Agent Engine and returns the final composed text.
3. Renders the returned message in the UI, or prints it to stdout in headless mode.

The point of this app: show that from a customer-app perspective, calling a Pantheon agent hosted on Vertex AI Agent Engine is **one method call** — indistinguishable from one hosted on Cloud Run. That is the AI-native PaaS abstraction working as designed.

## End-to-end call path

```
Flutter app                                       (this sample)
   │ client.agent.callVertexAgent(agentName: 'ceres', message: ...)
   ▼
Olympus Go API gateway                            (private monorepo)
   │ proxy /api/v1/agent/* → Python /api/agent/*
   ▼
Python agent_routes.py POST /agent/vertex/ceres   (PR #4957)
   │ vertexai.agent_engines.get(resource_name).stream_query(...)
   ▼
Vertex AI Agent Engine (managed runtime)          (olympuscloud-dev)
   │ root ceres agent → transfer_to_agent(levels_agent)
   │ load_inventory → evaluate_stock_levels → compose report
   ▼
Final composed text → all the way back up the stack → UI
```

## Status

Wire-ready. Works once these three are merged + deployed:

1. **PR `olympus-cloud-gcp#4957`** — gateway route
2. **PR `olympus-sdk-dart#144`** — SDK method
3. **This PR** — sample app uses the new method

…plus `../terraform` applied and `../adk/deploy.py` run (both already complete in `olympuscloud-dev`).
