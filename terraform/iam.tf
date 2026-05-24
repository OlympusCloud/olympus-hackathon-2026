locals {
  service_account_id = "pantheon-agent-engine-dev"
  resolved_sa_email = (
    var.create_service_account
    ? google_service_account.pantheon_agent_engine[0].email
    : var.service_account_email
  )
}

resource "google_service_account" "pantheon_agent_engine" {
  count = var.create_service_account ? 1 : 0

  account_id   = local.service_account_id
  display_name = "Pantheon Agent Engine (Ceres hackathon)"
  description  = "Identity for Ceres running on Vertex AI Agent Runtime. Reads/writes Memory Bank, calls Gemini via Ether."
  project      = var.project_id
}

# Minimum role set for Agent Runtime + Memory Bank. Do NOT broaden without
# revisiting; the carve-out repo is public and the IAM surface is auditable.
resource "google_project_iam_member" "agent_runtime_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${local.resolved_sa_email}"
}

resource "google_project_iam_member" "reasoning_engine_service_agent" {
  project = var.project_id
  role    = "roles/aiplatform.reasoningEngineServiceAgent"
  member  = "serviceAccount:${local.resolved_sa_email}"
}

resource "google_project_iam_member" "discovery_engine_editor" {
  project = var.project_id
  role    = "roles/discoveryengine.editor"
  member  = "serviceAccount:${local.resolved_sa_email}"
}

# Cloud Trace + Logging — for observability parity with the existing
# Pantheon Cloud Run substrate.
resource "google_project_iam_member" "trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${local.resolved_sa_email}"
}

resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${local.resolved_sa_email}"
}
