variable "db_url" {
  description = "The database connection URL"
  type        = string
  sensitive   = true
}

resource "google_secret_manager_secret" "db_url" {
  secret_id = "POSTGRES_URL"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_url_val" {
  secret      = google_secret_manager_secret.db_url.id
  secret_data = var.db_url
}
