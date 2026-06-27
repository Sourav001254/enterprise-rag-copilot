# terraform/main.tf
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "enterprise-rag-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "enterprise-rag"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

# Sub-modules for other resources (cloud_run, cloudsql, vpc) would be imported here or reside in the same directory.
