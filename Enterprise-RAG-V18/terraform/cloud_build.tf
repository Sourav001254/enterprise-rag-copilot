resource "google_cloudbuild_trigger" "api_build" {
  name = "api-trigger"
  
  github {
    owner = "your-org"
    name  = "enterprise-rag"
    push {
      branch = "^main$"
    }
  }

  filename = "cloudbuild.yaml"
}
