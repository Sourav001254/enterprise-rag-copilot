resource "google_sql_database_instance" "postgres" {
  name             = "enterprise-rag-db"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }
}

resource "google_sql_database" "rag_db" {
  name     = "rag_db"
  instance = google_sql_database_instance.postgres.name
}
