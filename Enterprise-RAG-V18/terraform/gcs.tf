resource "google_storage_bucket" "docs_bucket" {
  name          = "${var.project_id}-docs-bucket"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
}
