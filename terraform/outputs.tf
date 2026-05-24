output "service_account_email" {
  description = "Service account the Reasoning Engine runs as. Pass to ../adk/deploy.sh."
  value       = local.resolved_sa_email
}

output "memory_bank_data_stores" {
  description = "Map of tenant_id -> Memory Bank backing data store name. The per-tenant collections are the tenant-isolation primitive demonstrated in the demo."
  value       = { for k, v in google_discovery_engine_data_store.memory_bank : k => v.name }
}

output "next_step" {
  description = "What to run after apply completes."
  value       = "cd ../adk && ./deploy.sh   # deploys the Ceres Reasoning Engine via gcloud (Terraform provider does not yet expose google_vertex_ai_reasoning_engine)"
}
