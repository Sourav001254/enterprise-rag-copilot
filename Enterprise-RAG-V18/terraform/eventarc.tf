# Optional: Eventarc trigger when new file uploaded to GCS docs bucket
resource "google_eventarc_trigger" "gcs_trigger" {
  name     = "docs-upload-trigger"
  location = var.region

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }
  
  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.docs_bucket.name
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_v2_service.api.name
      path    = "/upload"
    }
  }
}
