"""Unified MCP wrapper for product spinning (shoes + other products)."""

import logging

from mcp_server.spinning.r2v.shoes.shoes_mcp import run_spinning_shoes_r2v
from mcp_server.spinning.r2v.other.other_mcp import run_spinning_other_r2v

logger = logging.getLogger(__name__)


async def run_product_spinning(
    images_base64: list[str],
    is_shoes: bool = False,
    max_retries: int = 5,
    veo_model: str = "veo-3.1-generate-001",
    product_id: str = "",
    gcs_bucket: str = "",
    gcs_destination_prefix: str = "spinning_outputs",
    gcs_project_id: str = "",
) -> dict:
    """Route to shoes or generic product spinning pipeline based on is_shoes flag.

    Args:
        images_base64: Base64-encoded product images from multiple angles.
        is_shoes: True for shoes pipeline (R2V with validation), False for generic products.
        max_retries: Max retries for video validation (shoes only). Default: 5.
        veo_model: Veo model for video generation (shoes only).
        product_id: Product identifier for GCS uploads (shoes only).
        gcs_bucket: GCS bucket for uploads (shoes only).
        gcs_destination_prefix: GCS prefix for uploads. Default: spinning_outputs.
        gcs_project_id: GCP project ID for GCS (shoes only).

    Returns:
        Dictionary with video_base64 and metadata.
    """
    if is_shoes:
        logger.info(f"[product_spinning] Routing to shoes pipeline ({len(images_base64)} images)")
        return await run_spinning_shoes_r2v(
            images_base64=images_base64,
            max_retries=max_retries,
            veo_model=veo_model,
            product_id=product_id,
            gcs_bucket=gcs_bucket,
            gcs_destination_prefix=gcs_destination_prefix,
            gcs_project_id=gcs_project_id,
        )
    else:
        logger.info(f"[product_spinning] Routing to generic pipeline ({len(images_base64)} images)")
        return await run_spinning_other_r2v(images_base64=images_base64)
