# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import sys

from google import genai
from google.cloud import storage
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ==============================================================================
# Configuration Logic (Pydantic)
# ==============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)


def get_logger(name: str):
    """Returns a standard Python logger."""
    return logging.getLogger(name)


log = get_logger("config")


class AppConfig(BaseSettings):
    google_cloud_project: str = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_CLOUD_PROJECT", "GCP_PROJECT"),
    )
    google_cloud_location: str = Field(
        default="us-central1",
        validation_alias=AliasChoices("GOOGLE_CLOUD_LOCATION", "GCP_LOCATION"),
    )
    gemini_model_name: str = Field(
        default="gemini-2.5-flash", alias="GEMINI_MODEL_NAME"
    )
    image_generation_model: str = Field(
        default="imagen-3.0-generate-002", alias="IMAGE_GENERATION_MODEL"
    )
    google_cloud_project_number: str | None = None
    gcp_staging_bucket: str | None = Field(
        default=None, alias="GCP_STAGING_BUCKET"
    )
    default_template_uri: str | None = Field(
        default=None, alias="DEFAULT_TEMPLATE_URI"
    )
    datastore_id: str | None = Field(default=None, alias="DATASTORE_ID")

    enable_rag: bool = Field(default=False, alias="ENABLE_RAG")
    enable_deep_research: bool = Field(
        default=False, alias="ENABLE_DEEP_RESEARCH"
    )
    model_armor_template_id: str | None = Field(
        default=None, alias="MODEL_ARMOR_TEMPLATE_ID"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# Initialize configuration
try:
    config = AppConfig()
except Exception as e:
    log.error(f"Configuration validation failed: {e}")
    raise

# Exported Config Variables
PROJECT_ID = config.google_cloud_project
PROJECT_NUMBER = config.google_cloud_project_number
LOCATION = config.google_cloud_location
ROOT_MODEL = config.gemini_model_name
IMAGE_GENERATION_MODEL = config.image_generation_model
ENABLE_RAG = config.enable_rag
ENABLE_DEEP_RESEARCH = config.enable_deep_research
MODEL_ARMOR_TEMPLATE_ID = config.model_armor_template_id
DATASTORE_ID = config.datastore_id
DEFAULT_TEMPLATE_URI = config.default_template_uri

# Format GCS Bucket Name
GCS_BUCKET_NAME = config.gcp_staging_bucket
if GCS_BUCKET_NAME:
    # Safely strip prefix and trailing slashes
    GCS_BUCKET_NAME = GCS_BUCKET_NAME.replace("gs://", "").strip("/")
    # Ensure we only take the root bucket name if a path was provided
    GCS_BUCKET_NAME = GCS_BUCKET_NAME.split("/")[0]

PRESENTATION_SPEC_ARTIFACT = "presentation_spec.json"
RESEARCH_SUMMARY_ARTIFACT = "research_summary.txt"

# Global genai client, initialized via function
_genai_client = None

# ==============================================================================
# Client Initialization and Logging Utilities
# ==============================================================================


def initialize_genai_client():
    """Initializes and returns the global Vertex AI GenAI client."""
    global _genai_client
    if _genai_client is None:
        try:
            _genai_client = genai.Client(
                vertexai=True, project=PROJECT_ID, location=LOCATION
            )
            log.info(
                f"Vertex AI client initialized for project '{PROJECT_ID}' in location '{LOCATION}'."
            )
        except Exception as e:
            log.error(f"CRITICAL: Failed to initialize Vertex AI client: {e}")
            _genai_client = None
    return _genai_client


def get_gcs_client():
    """Initializes and returns a GCS client with robust project detection."""
    try:
        # If PROJECT_ID is provided, use it; otherwise, let the SDK auto-detect
        if PROJECT_ID:
            client = storage.Client(project=PROJECT_ID)
        else:
            client = storage.Client()
        return client
    except Exception as e:
        get_logger("get_gcs_client").error(
            f"Failed to initialize GCS client: {e}"
        )
        get_logger("get_gcs_client").warning(
            "Please ensure you are authenticated (e.g., `gcloud auth application-default login`)"
        )
        return None
