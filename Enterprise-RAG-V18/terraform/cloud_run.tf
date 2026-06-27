resource "google_cloud_run_v2_service" "api" {
  name     = "enterprise-rag-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "us-central1-docker.pkg.dev/${var.project_id}/rag-repo/api:latest"
      
      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }
      
      env {
        name = "POSTGRES_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_url.secret_id
            version = "latest"
          }
        }
      }
      
      # Other env vars omitted for brevity but they follow the same pattern
    }
    
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }
}
