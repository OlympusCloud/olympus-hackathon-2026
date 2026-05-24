# `sdk/dart-sample/` — minimal Flutter app calling hosted Ceres

Output of hackathon work item **H7** (expose hosted Ceres via `olympus_sdk` — gateway route + Dart SDK).

## What lands here

A tiny Flutter app that:

1. Authenticates against the Olympus API gateway with a demo tenant JWT.
2. Calls `olympusSdk.ai.runAgent('ceres', query: 'low-stock report')`.
3. Renders the returned `Report` + `recommendations` + `stock_alerts` in a stripped-down list view.

The point: show that from a customer app's perspective, calling a Pantheon agent that happens to be hosted on Vertex AI Agent Runtime is **one method call**, indistinguishable from calling one hosted on Cloud Run. That is the AI-native PaaS abstraction working as designed.

## Dependencies

- `olympus_sdk` (git dep — `git: url: https://github.com/OlympusCloud/olympus-sdk-dart`)
- Flutter ≥ 3.27 stable
- A demo tenant JWT (issued at demo time; not shipped)

## Files

- `pubspec.yaml` — SDK git dep + Flutter
- `lib/main.dart` — `MyApp` + the single screen
- `lib/demo_credentials.dart.example` — template; copy to `demo_credentials.dart` (gitignored)
- `test/ceres_call_test.dart` — one widget test verifying the SDK call wiring

## Run

```bash
cd sdk/dart-sample
flutter pub get
cp lib/demo_credentials.dart.example lib/demo_credentials.dart
# fill in OLYMPUS_GATEWAY_URL + DEMO_TENANT_JWT
flutter run -d chrome
```

## Status

⬜ Pending — waiting on H5 (deployed agent) + H7 (gateway route landing in private monorepo).
