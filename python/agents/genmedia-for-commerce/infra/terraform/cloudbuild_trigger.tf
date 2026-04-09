# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Cloud Build Trigger for automatic deployments
# Only created if repo_provider is set

resource "google_cloudbuild_trigger" "deploy" {
  count    = var.repo_provider != "" ? 1 : 0
  name     = "deploy-${var.service_name}"
  location = var.region

  # GitHub configuration
  dynamic "github" {
    for_each = var.repo_provider == "github" ? [1] : []
    content {
      owner = var.repo_owner
      name  = var.repo_name
      push {
        branch = var.repo_branch
      }
    }
  }

  # GitLab configuration
  dynamic "repository_event_config" {
    for_each = var.repo_provider == "gitlab" ? [1] : []
    content {
      repository = "projects/${var.repo_owner}/${var.repo_name}"
      push {
        branch = var.repo_branch
      }
    }
  }

  filename        = "cloudbuild.yaml"
  service_account = google_service_account.cloudbuild.id

  substitutions = {
    _SERVICE       = var.service_name
    _REGION        = var.region
    _REPO          = "${var.service_name}-repo"
    _MEMORY        = var.memory
    _CPU           = var.cpu
    _TIMEOUT       = tostring(var.timeout)
    _CONCURRENCY   = tostring(var.concurrency)
    _MIN_INSTANCES = tostring(var.min_instances)
    _MAX_INSTANCES = tostring(var.max_instances)
  }

  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.docker
  ]
}
