resource "google_cloud_scheduler_job" "ingestion_cron" {
  name             = "nightly-ingestion"
  description      = "Trigger Cloud Run Ingestion Job nightly"
  schedule         = "0 2 * * *"
  time_zone        = "America/New_York"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/rag-ingestion:run"
    
    oauth_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }
}

resource "google_service_account" "scheduler_sa" {
  account_id   = "scheduler-sa"
  display_name = "Cloud Scheduler SA"
}
