output "api_url" {
  value = google_cloud_run_v2_service.api.uri
}

output "db_instance_ip" {
  value = google_sql_database_instance.postgres.private_ip_address
}
