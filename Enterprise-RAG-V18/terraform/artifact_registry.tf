resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "rag-repo"
  description   = "Docker repository for Enterprise RAG"
  format        = "DOCKER"
}
