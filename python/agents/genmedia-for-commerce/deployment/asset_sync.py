"""Push binary assets to GCS.

Assets (images, model weights, videos) are too large for Agent Engine's 8MB
source-package limit and for the public git repo.  This script uploads them
to a GCS bucket:

  make push-assets   uploads local binaries → GCS

Pull is handled automatically by config.py at import time.

Assets live under assets/backend_assets/ and assets/frontend_assets/ in the
project root.  The GCS bucket name is computed from a seed hash (same pattern
as the catalogue in vector_search.py) so it is never hardcoded.
"""

import io
import logging
import os
import tarfile
from pathlib import Path

from google.cloud import storage

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GCS coordinates (imported from config to stay in sync)
# ---------------------------------------------------------------------------
from genmedia4commerce.config import (
    ASSETS_DIR,
    BACKEND_ASSETS_DIR,
    FRONTEND_ASSETS_DIR,
    _ASSET_BUCKET as _BUCKET,
    _ASSET_PREFIX as _GCS_PREFIX,
    _BACKEND_ASSETS_TAR,
    _FRONTEND_ASSETS_TAR,
)


def _get_client():
    project_id = os.environ.get("PROJECT_ID")
    return storage.Client(project=project_id)


def _create_dir_tar(
    directory: Path, base_dir: Path, exclude_patterns: list[str] | None = None
) -> bytes:
    """Create an in-memory tar.gz of a directory, optionally excluding files."""

    def _filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
        if exclude_patterns:
            name = Path(tarinfo.name).name
            for pattern in exclude_patterns:
                if name.startswith(pattern):
                    return None
        return tarinfo

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(
            str(directory),
            arcname=str(directory.relative_to(base_dir)),
            filter=_filter,
        )
    return buf.getvalue()


def _upload(client: storage.Client, tar_bytes: bytes, tar_name: str):
    bucket = client.bucket(_BUCKET)
    blob = bucket.blob(f"{_GCS_PREFIX}/{tar_name}")
    blob.upload_from_string(tar_bytes, content_type="application/gzip")
    size_mb = len(tar_bytes) / (1024 * 1024)
    logger.info(f"  Uploaded {tar_name} ({size_mb:.1f} MB) → gs://{_BUCKET}/{_GCS_PREFIX}/{tar_name}")


def main():
    """Upload binary assets to GCS."""
    client = _get_client()

    # Backend assets (embeddings excluded — pulled separately by vector_search.py)
    if BACKEND_ASSETS_DIR.exists():
        file_count = sum(1 for _ in BACKEND_ASSETS_DIR.rglob("*") if _.is_file())
        logger.info(f"Packing backend asset files (excluding embeddings*.npy)...")
        tar_bytes = _create_dir_tar(
            BACKEND_ASSETS_DIR, ASSETS_DIR, exclude_patterns=["embeddings"]
        )
        _upload(client, tar_bytes, _BACKEND_ASSETS_TAR)
    else:
        logger.info(f"Backend assets not found at {BACKEND_ASSETS_DIR}, skipping")

    # Frontend assets
    if FRONTEND_ASSETS_DIR.exists():
        file_count = sum(1 for _ in FRONTEND_ASSETS_DIR.rglob("*") if _.is_file())
        logger.info(f"Packing {file_count} frontend asset files...")
        tar_bytes = _create_dir_tar(FRONTEND_ASSETS_DIR, ASSETS_DIR)
        _upload(client, tar_bytes, _FRONTEND_ASSETS_TAR)
    else:
        logger.info(f"Frontend assets not found at {FRONTEND_ASSETS_DIR}, skipping")

    logger.info("Push complete.")


if __name__ == "__main__":
    main()
