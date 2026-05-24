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
2. Calls `client.agent.chat(...)` — the existing canonical agent surface in `olympus_sdk`. The gateway routes the request to the hosted Ceres agent on Vertex AI Agent Runtime.
3. Renders the returned message in the UI, or prints it to stdout in headless mode.

The point of this app: show that from a customer-app perspective, calling a Pantheon agent that happens to be hosted on Vertex AI Agent Runtime is **one method call**, indistinguishable from calling one hosted on Cloud Run. That is the AI-native PaaS abstraction working as designed.

## Status

Wire-ready. Will work as soon as:

1. Terraform has applied (see `../terraform/README-deploy.md`)
2. ADK manifest has deployed (see `../adk/deploy.sh`)
3. A demo tenant JWT has been minted and dropped into `demo_credentials.dart`
