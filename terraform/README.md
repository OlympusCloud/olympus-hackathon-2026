# `terraform/` — Vertex AI Agent Builder + Memory Bank + IAM (dev)

Output of hackathon work item **H4** (Terraform module). Sanitized for public release per the IP gate in [`../SECURITY.md`](../SECURITY.md).

## What lands here

- `main.tf` — `google_vertex_ai_reasoning_engine` + `google_discovery_engine_data_store` (Memory Bank backing store) resource definitions.
- `iam.tf` — service account + role bindings for `pantheon-agent-engine-dev`.
- `variables.tf` — `project_id`, `region`, `tenant_count` (for the multi-tenant Memory Bank collections).
- `outputs.tf` — agent endpoint URL, Memory Bank collection IDs (one per demo tenant).
- `versions.tf` — provider pins.
- `README-deploy.md` — step-by-step apply guide.

## Out of scope (intentionally absent)

- Per-environment `terraform.tfstate` (this module ships **template only**; state stays in private GCS).
- `terraform.tfvars` with real project IDs / org IDs / billing accounts.
- Shared-services account bindings (Artifact Registry, secret-manager parents).
- The CI/CD pipeline that runs `terraform apply` in dev (lives in the private monorepo's `.github/workflows/`).

## Status

⬜ Pending — waiting on H1 (Vertex APIs enabled in `olympuscloud-dev` + service account created per [`../SCOTT-ACTION-REQUIRED.md`](../SCOTT-ACTION-REQUIRED.md)).

## Apply (when ready)

```bash
cd terraform
terraform init
terraform plan -var project_id=olympuscloud-dev -var region=us-central1
terraform apply
```

The agent endpoint URL from `terraform output` feeds into [`../adk/deploy.sh`](../adk/) and [`../sdk/dart-sample/`](../sdk/dart-sample/).
