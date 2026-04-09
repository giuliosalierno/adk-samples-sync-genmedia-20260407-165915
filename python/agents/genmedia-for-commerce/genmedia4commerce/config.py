# Copyright 2025 Google LLC
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

"""GenMedia for Commerce configuration.

Handles authentication, environment setup, and asset downloads.
Imported by agent.py at startup.
"""

import hashlib
import io
import logging
import os
import tarfile
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from config.env
env_path = Path(__file__).parent / "config.env"
load_dotenv(dotenv_path=env_path)

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

if os.getenv("GOOGLE_API_KEY"):
    # AI Studio mode: Use API key authentication
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")
else:
    # Vertex AI mode: Use PROJECT_ID from config.env, fall back to ADC
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        import google.auth
        _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
    os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GLOBAL_REGION", "global")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

# GCS bucket computed from seed hash (same as catalogue in vector_search.py)
_ASSET_SEED = "genmedia_for_commerce_generated_fashion_images"
_ASSET_BUCKET = hashlib.sha256(_ASSET_SEED.encode()).hexdigest()[:63]
_ASSET_PREFIX = "genmedia_for_commerce_repo_assets"
_BACKEND_ASSETS_TAR = "backend_assets.tar.gz"
_FRONTEND_ASSETS_TAR = "frontend_assets.tar.gz"

# Local assets directory (project root / assets)
ASSETS_DIR = Path(__file__).parent.parent / "assets"
BACKEND_ASSETS_DIR = ASSETS_DIR / "backend_assets"
FRONTEND_ASSETS_DIR = ASSETS_DIR / "frontend_assets"

# Files that must exist to consider each asset set complete.
_BACKEND_REQUIRED = [
    BACKEND_ASSETS_DIR / "catalogue" / "metadata.parquet",
]
_FRONTEND_REQUIRED: list[Path] = []


def _pull_tar(
    tar_name: str, target_dir: Path, required_files: list[Path] | None = None
):
    """Download and extract a single asset tar from GCS if not present locally."""
    if target_dir.exists() and any(target_dir.iterdir()):
        missing = [f for f in (required_files or []) if not f.exists()]
        if not missing:
            logger.info(f"{target_dir.name} already present, skipping download")
            return
        logger.info(
            f"{target_dir.name} incomplete (missing {len(missing)} files), re-downloading"
        )

    logger.info(f"Downloading {tar_name} from GCS...")
    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(_ASSET_BUCKET)
        blob = bucket.blob(f"{_ASSET_PREFIX}/{tar_name}")

        if not blob.exists():
            logger.warning(
                f"{tar_name} not found in GCS — run 'make push-assets' to upload"
            )
            return

        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        tar_bytes = blob.download_as_bytes()
        buf = io.BytesIO(tar_bytes)
        with tarfile.open(fileobj=buf, mode="r:gz") as tar:
            tar.extractall(path=str(ASSETS_DIR))

        size_mb = len(tar_bytes) / (1024 * 1024)
        logger.info(f"Extracted {tar_name} ({size_mb:.1f} MB) to {target_dir}")
    except Exception as e:
        logger.warning(f"Could not download {tar_name}: {e}")


def pull_assets():
    """Download all assets from GCS if not present locally.

    Called automatically at import time. No-op when assets already exist
    (e.g. local dev with assets on disk, or Docker with COPY assets/).
    """
    _pull_tar(_BACKEND_ASSETS_TAR, BACKEND_ASSETS_DIR, _BACKEND_REQUIRED)
    _pull_tar(_FRONTEND_ASSETS_TAR, FRONTEND_ASSETS_DIR, _FRONTEND_REQUIRED)


# ---------------------------------------------------------------------------
# Media storage bucket (user uploads & AI outputs)
# ---------------------------------------------------------------------------


def _ensure_media_bucket() -> str:
    """Create the media bucket if it doesn't exist. Returns bucket name."""
    project_id = os.getenv("PROJECT_ID", "")
    default_bucket = (
        f"{project_id}-genmedia-for-commerce-media-payloads"
        if project_id
        else "genmedia-for-commerce-media-payloads"
    )
    bucket_name = os.getenv("MEDIA_BUCKET", default_bucket)
    try:
        from google.cloud import storage

        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        if not bucket.exists():
            logger.info(f"Creating media bucket: {bucket_name} in project {project_id}")
            client.create_bucket(
                bucket_name,
                project=project_id,
                location=os.getenv("DEFAULT_REGION", "us-central1"),
            )
            logger.info(f"Created media bucket: {bucket_name}")
        else:
            logger.info(f"Media bucket already exists: {bucket_name}")
    except Exception as e:
        logger.warning(f"Could not ensure media bucket: {e}")
    return bucket_name


MEDIA_BUCKET = _ensure_media_bucket()

# ---------------------------------------------------------------------------
# Shared Gemini client (reused across agent utilities)
# ---------------------------------------------------------------------------
from google import genai  # noqa: E402

genai_client = genai.Client(
    vertexai=True,
    project=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class GenMediaConfig:
    """Configuration for GenMedia agent.

    Attributes:
        agent_model: Model for the router agent.
        mcp_server_url: URL of the MCP server (SSE endpoint).
    """

    agent_model: str = "gemini-2.5-flash"
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "http://localhost:8081/sse")


config = GenMediaConfig()

# ---------------------------------------------------------------------------
# Auto-download assets at import time (no-op if already on disk)
# ---------------------------------------------------------------------------
pull_assets()
