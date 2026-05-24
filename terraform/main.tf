# Vertex AI Agent Builder supporting infrastructure for the hackathon
# Ceres deployment. Sanitized for the public carve-out:
# - no per-environment state (state lives in private GCS)
# - no shared-services bindings (Artifact Registry, secret-manager parents)
# - no real tenant ids (defaults are 'demo-tenant-a' / 'demo-tenant-b')
#
# Scope of this Terraform module:
#   - Required GCP APIs
#   - Service account + minimum IAM roles (see iam.tf)
#   - One Discovery Engine data store per demo tenant — backs Agent
#     Memory Bank, gives us the per-tenant collection boundary the demo
#     uses to prove isolation.
#
# Out of scope (handled by ../adk/deploy.sh via gcloud):
#   - The Vertex AI Reasoning Engine instance that runs the Ceres ADK
#     manifest. The hashicorp/google provider does not yet expose a
#     `google_vertex_ai_reasoning_engine` resource (Agent Builder /
#     Agent Engine launched after the provider's current Vertex AI
#     resource catalog). We provision via `gcloud ai reasoning-engines
#     deploy` until the provider lands a resource type for it; migrating
#     to managed Terraform is straightforward when that ships.

# Required APIs. These are also called out in ../SCOTT-ACTION-REQUIRED.md
# as a maintainer manual step, but we declare them here so re-applies are
# self-healing if someone disables them by accident.
resource "google_project_service" "aiplatform" {
  project            = var.project_id
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "discovery_engine" {
  project            = var.project_id
  service            = "discoveryengine.googleapis.com"
  disable_on_destroy = false
}

# One Memory Bank backing data store per demo tenant. The per-tenant
# collection boundary is the "tenant isolation" primitive we demonstrate
# in the demo: tenant A's agent run cannot read tenant B's memory because
# they live in different data stores under different IAM principals.
#
# Each data store is provisioned with no content + the SOLUTION_TYPE_CHAT
# solution type, which is the canonical pattern for backing an Agent
# Builder / Memory Bank collection.
resource "google_discovery_engine_data_store" "memory_bank" {
  provider = google-beta
  for_each = toset(var.memory_bank_tenants)

  project           = var.project_id
  location          = "global"
  data_store_id     = "ceres-memory-${each.key}"
  display_name      = "Ceres Memory Bank — ${each.key}"
  industry_vertical = "GENERIC"
  content_config    = "NO_CONTENT"
  solution_types    = ["SOLUTION_TYPE_CHAT"]

  depends_on = [google_project_service.discovery_engine]
}
