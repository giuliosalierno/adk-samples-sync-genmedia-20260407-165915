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

# =============================================================================
# Project data
# =============================================================================

data "google_project" "project" {}

locals {
  cloudrun_sa    = "serviceAccount:${google_service_account.cloudrun.email}"
  aiplatform_re  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
}

# =============================================================================
# Cloud Build service agent (P4SA)
# =============================================================================

resource "google_project_service_identity" "cloudbuild" {
  provider = google-beta
  project  = var.project_id
  service  = "cloudbuild.googleapis.com"

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "cloudbuild" {
  for_each = toset([
    "roles/storage.admin",
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.admin",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_project_service_identity.cloudbuild.email}"
}

# =============================================================================
# Dedicated Cloud Build service account (replaces default Compute SA)
# =============================================================================

resource "google_service_account" "cloudbuild" {
  account_id   = "genmedia-cloudbuild"
  display_name = "GenMedia Cloud Build Service Account"
  project      = var.project_id

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "cloudbuild_sa" {
  for_each = toset([
    "roles/storage.admin",
    "roles/artifactregistry.admin",
    "roles/logging.logWriter",
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# =============================================================================
# Dedicated Cloud Run service account (runtime identity)
# =============================================================================

resource "google_service_account" "cloudrun" {
  account_id   = "genmedia-cloudrun"
  display_name = "GenMedia Cloud Run Service Account"
  project      = var.project_id

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "cloudrun" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/storage.admin",
    "roles/logging.logWriter",
    "roles/artifactregistry.admin",
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
  ])

  project = var.project_id
  role    = each.value
  member  = local.cloudrun_sa
}

# =============================================================================
# AI Platform / Agent Engine service agents
# =============================================================================

resource "google_project_service_identity" "aiplatform" {
  provider = google-beta
  project  = var.project_id
  service  = "aiplatform.googleapis.com"

  depends_on = [google_project_service.apis]
}

# General AI Platform service agent
resource "google_project_iam_member" "aiplatform" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_project_service_identity.aiplatform.email}"
}

# Reasoning Engine service agent (Agent Engine runtime)
resource "google_project_iam_member" "aiplatform_re" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = local.aiplatform_re

  depends_on = [google_project_service.apis]
}
