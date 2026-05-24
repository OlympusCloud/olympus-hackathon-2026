# Deploy guide — Vertex AI Agent Builder for Ceres

## Prerequisites

See `../SCOTT-ACTION-REQUIRED.md` for the one-time maintainer steps (enabling APIs, IAM, GCS credit confirmation). When those are clear, the apply below is mechanical.

## Plan

```bash
cd terraform
terraform init
terraform plan -var project_id=olympuscloud-dev
```

Expect roughly:
- 2 `google_project_service` (aiplatform, discoveryengine) — no-op if already enabled
- 1 `google_service_account` (pantheon-agent-engine-dev) — no-op if already created out-of-band
- 5 `google_project_iam_member` (aiplatform.user, reasoningEngineServiceAgent, discoveryengine.editor, cloudtrace.agent, logging.logWriter)
- 2 `google_discovery_engine_data_store` (one per demo tenant) — the Memory Bank tenant-isolation primitive

Total ~10 resources for the dev environment.

The Reasoning Engine instance itself is **not** provisioned by this module — the `hashicorp/google` provider does not yet expose a `google_vertex_ai_reasoning_engine` resource (Agent Builder / Agent Engine launched after the provider's current Vertex AI resource catalog). It is deployed via `gcloud ai reasoning-engines deploy` from `../adk/deploy.sh` as a follow-on step. We will migrate to managed Terraform when the provider adds support.

## Apply

```bash
terraform apply -var project_id=olympuscloud-dev
```

## After apply

1. Capture outputs:

   ```bash
   terraform output service_account_email
   terraform output -json memory_bank_data_stores
   ```

2. Deploy the ADK manifest as a new reasoning engine (this is the step the Terraform module deliberately skips, see above):

   ```bash
   cd ../adk
   ./deploy.sh
   ```

3. Wire `../sdk/dart-sample/lib/demo_credentials.dart` with the endpoint + a demo tenant JWT.

4. Run `make demo` from the repo root.

## Tear-down

```bash
terraform destroy -var project_id=olympuscloud-dev
```

The `disable_on_destroy = false` on the API enablement resources is intentional — destroying the agent should not also turn off APIs other services in the project depend on.
