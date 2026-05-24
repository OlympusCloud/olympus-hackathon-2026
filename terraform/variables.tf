variable "project_id" {
  description = "Target GCP project (e.g. olympuscloud-dev)."
  type        = string
}

variable "region" {
  description = "Region for Vertex AI Agent Builder + Agent Runtime + Memory Bank."
  type        = string
  default     = "us-central1"
}

variable "agent_name" {
  description = "Reasoning Engine instance name. Override for staging / per-environment instances."
  type        = string
  default     = "ceres-dev"
}

variable "memory_bank_tenants" {
  description = "Demo tenant ids. One Memory Bank collection is provisioned per tenant for the hackathon demo's tenant-isolation proof."
  type        = list(string)
  default     = ["demo-tenant-a", "demo-tenant-b"]

  validation {
    condition     = length(var.memory_bank_tenants) >= 2
    error_message = "Need at least two tenants to demonstrate isolation."
  }
}

variable "service_account_email" {
  description = "Service account used by Agent Runtime to call Vertex AI + Memory Bank. Created in iam.tf if create_service_account=true."
  type        = string
  default     = null
}

variable "create_service_account" {
  description = "If true, this module creates the service account. If false, it expects var.service_account_email to point at an existing one."
  type        = bool
  default     = true
}

variable "labels" {
  description = "Labels applied to every resource (cost attribution + tear-down hygiene)."
  type        = map(string)
  default = {
    "olympus.hackathon" = "2026"
    "olympus.agent"     = "ceres"
    "olympus.env"       = "dev"
    "managed-by"        = "terraform"
  }
}
