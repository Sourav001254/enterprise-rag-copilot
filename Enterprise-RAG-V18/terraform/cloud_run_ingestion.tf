resource "google_cloud_run_v2_job" "ingestion" {
  name     = "rag-ingestion"
  location = var.region

  template {
    template {
      containers {
        image = "us-central1-docker.pkg.dev/${var.project_id}/rag-repo/ingestion:latest"
        
        env {
          name = "POSTGRES_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_url.secret_id
              version = "latest"
            }
          }
        }
      }
      
      vpc_access {
        connector = google_vpc_access_connector.connector.id
        egress    = "ALL_TRAFFIC"
      }
    }
  }
}
