"""Generate and upload embedding variants to GCS.

Uploads the full embeddings.npy plus normalized, truncated copies at various
dimensions (128, 256, 512, 1024) as separate .npy files to the asset bucket
under catalogue/.

Usage:
    uv run python infra/push_truncated_embeddings.py
"""

import io
import logging
import os

import numpy as np
from google.cloud import storage

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

from genmedia4commerce.config import (
    BACKEND_ASSETS_DIR,
    _ASSET_BUCKET as _BUCKET,
    _ASSET_PREFIX as _GCS_PREFIX,
)

DIMS = [128, 256, 512, 1024]
SRC = BACKEND_ASSETS_DIR / "catalogue" / "embeddings.npy"


def _upload_npy(bucket, blob_path: str, arr: np.ndarray):
    """Upload a numpy array as a proper .npy file to GCS."""
    buf = io.BytesIO()
    np.save(buf, arr)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(buf.getvalue(), content_type="application/octet-stream")


def main():
    logger.info(f"Loading full embeddings from {SRC}")
    full = np.load(SRC)
    logger.info(f"Shape: {full.shape}, dtype: {full.dtype}")

    client = storage.Client(project=os.environ.get("PROJECT_ID"))
    bucket = client.bucket(_BUCKET)

    # Upload the full embeddings as a standalone blob
    full_path = f"{_GCS_PREFIX}/catalogue/embeddings.npy"
    size_mb = full.nbytes / 1024 / 1024
    logger.info(f"  {full.shape[1]:>5}d  {full.shape}  {size_mb:.1f} MB → gs://{_BUCKET}/{full_path}")
    _upload_npy(bucket, full_path, full)

    # Upload truncated + normalized variants
    for d in DIMS:
        truncated = full[:, :d].copy()
        norms = np.linalg.norm(truncated, axis=1, keepdims=True)
        norms[norms == 0] = 1
        truncated = (truncated / norms).astype(np.float32)

        blob_path = f"{_GCS_PREFIX}/catalogue/embeddings_{d}d.npy"
        size_mb = truncated.nbytes / 1024 / 1024
        logger.info(f"  {d:>5}d  {truncated.shape}  {size_mb:.1f} MB → gs://{_BUCKET}/{blob_path}")
        _upload_npy(bucket, blob_path, truncated)

    logger.info("Done.")


if __name__ == "__main__":
    main()
