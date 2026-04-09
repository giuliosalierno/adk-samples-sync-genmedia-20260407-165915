"""REST API endpoint for the product fitting workflow (catalogue enrichment)."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mcp_server.product_enrichment.product_fitting.product_fitting_mcp import run_product_fitting

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/product-enrichment/product-fitting",
    tags=["Product Fitting"],
)


class ProductFittingRequest(BaseModel):
    garment_images_base64: list[str] = Field(
        ..., description="List of base64-encoded garment product images"
    )
    gender: str = Field(..., description="Model gender: man or woman")
    ethnicity: str = Field(
        default="european", description="Model ethnicity preset: african, asian, european"
    )
    scenario: str = Field(
        default="a pure white background (#FFFFFF), no shadows, no gradients",
        description="Background description for the generated image",
    )
    max_retries: int = Field(default=3, description="Maximum generation attempts per view")
    generation_model: str = Field(
        default="gemini-3.1-flash-image-preview",
        description="Gemini model for image generation",
    )
    product_id: str = Field(default="", description="Optional product identifier")
    model_photos: dict[str, str] | None = Field(
        default=None,
        description="Optional custom model photos as base64. "
        "Keys: front_top, front_bottom. If provided, ethnicity preset is ignored.",
    )


@router.post("/generate-fitting-pipeline")
async def generate_fitting_pipeline(request: ProductFittingRequest) -> dict:
    """Generate product fitting images for catalogue enrichment.

    Takes a single garment's product photos and generates realistic images of that
    garment worn on an AI model body (front and back views). Designed for B2B
    catalogue imagery — for B2C virtual try-on with multiple garments on a real
    person, use the image VTO endpoint instead.
    """
    if not request.garment_images_base64:
        raise HTTPException(status_code=400, detail="Missing 'garment_images_base64' in request body.")

    if not request.gender:
        raise HTTPException(status_code=400, detail="'gender' is required (e.g. man, woman).")

    if not request.model_photos and not request.ethnicity:
        raise HTTPException(
            status_code=400,
            detail="Must provide either 'ethnicity' (with 'gender') or 'model_photos' "
            "(dict with keys: front_top, front_bottom).",
        )

    logger.info(
        f"[REST product_fitting] Called with {len(request.garment_images_base64)} images, "
        f"gender={request.gender}, ethnicity={request.ethnicity}"
    )

    result = await run_product_fitting(
        garment_images_base64=request.garment_images_base64,
        gender=request.gender,
        ethnicity=request.ethnicity,
        scenario=request.scenario,
        max_retries=request.max_retries,
        generation_model=request.generation_model,
        product_id=request.product_id,
        model_photos=request.model_photos,
    )

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    logger.info(f"[REST product_fitting] Complete. Keys: {list(result.keys())}")
    return result
