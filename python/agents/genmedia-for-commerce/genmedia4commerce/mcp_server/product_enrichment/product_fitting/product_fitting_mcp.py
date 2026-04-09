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

"""MCP tool wrapper for the product fitting pipeline (catalogue enrichment)."""

import base64
import logging
import os
from pathlib import Path

from google import genai

from workflows.product_enrichment.product_fitting.pipeline import run_fitting_pipeline

logger = logging.getLogger(__name__)

# Model photo presets directory
from genmedia4commerce.config import BACKEND_ASSETS_DIR

MODELS_DIR = BACKEND_ASSETS_DIR / "product_enrichment" / "product_fitting" / "models"
REQUIRED_MODEL_PHOTOS = {"front_top", "front_bottom"}

# Available presets (discovered at import time)
AVAILABLE_PRESETS = []
if MODELS_DIR.exists():
    AVAILABLE_PRESETS = sorted(d.name for d in MODELS_DIR.iterdir() if d.is_dir())


def _get_clients():
    """Create genai clients from environment variables."""
    project_id = os.getenv("PROJECT_ID", "my_project")
    global_region = os.getenv("GLOBAL_REGION", "global")
    genai_client = genai.Client(vertexai=True, project=project_id, location=global_region)
    nano_client = genai.Client(
        vertexai=True, project=project_id, location=global_region
    )
    return genai_client, nano_client


def _load_preset_model_photos(ethnicity: str, gender: str) -> dict[str, bytes]:
    """Load model photos from preset folder."""
    gender_map = {"man": "man", "male": "man", "woman": "woman", "female": "woman", "boy": "boy", "girl": "girl"}
    gender_key = gender_map.get(gender.lower(), gender.lower())
    folder = MODELS_DIR / f"{ethnicity.lower()}_{gender_key}"
    if not folder.exists():
        raise ValueError(
            f"No model preset for ethnicity='{ethnicity}', gender='{gender}'. "
            f"Available presets: {AVAILABLE_PRESETS}"
        )
    photos = {}
    for name in REQUIRED_MODEL_PHOTOS:
        photo_path = folder / f"{name}.png"
        if not photo_path.exists():
            raise ValueError(f"Missing model photo: {photo_path}")
        photos[name] = photo_path.read_bytes()
    return photos


async def run_product_fitting(
    garment_images_base64: list[str],
    gender: str,
    ethnicity: str = "european",
    scenario: str = "a pure white background (#FFFFFF), no shadows, no gradients",
    max_retries: int = 3,
    generation_model: str = "gemini-3.1-flash-image-preview",
    product_id: str = "",
    model_photos: dict[str, str] | None = None,
) -> dict:
    """Generate product fitting images for catalogue enrichment (B2B).

    Product fitting is designed for enriching product catalogues: it takes
    a single garment's product photos and generates realistic images of that
    garment worn on an AI-generated model body, producing both front and back
    views. Unlike Virtual Try-On (VTO) which dresses a real person in multiple
    garments (B2C), product fitting showcases one product at a time on a
    preset AI model for catalogue imagery.

    Args:
        garment_images_base64: List of base64-encoded garment product images.
            At least one image required. Include front and back views for best results.
        gender: Model gender. One of: man, woman.
        ethnicity: Model ethnicity preset. One of: african, asian, european.
            Default: european. Ignored if model_photos is provided.
        scenario: Background description for the generated image.
            Default: pure white background.
        max_retries: Maximum generation attempts per view. Default: 3.
        generation_model: Gemini model for generation. Default: gemini-3.1-flash-image-preview.
        product_id: Optional product identifier for logging.
        model_photos: Optional dict mapping photo name to base64 string.
            Keys must be: front_top, front_bottom. If provided, ethnicity preset is ignored.

    Returns:
        Dictionary with front and back results including image_base64, status, and validation.
    """
    if not garment_images_base64:
        return {"error": "At least one garment image is required."}

    def _decode_image(val: str, label: str) -> bytes | str:
        """Decode base64 to bytes, or pass through gs:// URIs as-is."""
        if val.startswith("gs://"):
            return val
        try:
            return base64.b64decode(val)
        except Exception as e:
            raise ValueError(f"Invalid base64 for {label}: {e}")

    garment_images_bytes: list[bytes | str] = []
    for idx, img_b64 in enumerate(garment_images_base64):
        try:
            garment_images_bytes.append(_decode_image(img_b64, f"garment image {idx}"))
        except ValueError as e:
            return {"error": str(e)}

    # Resolve model photos: custom dict or preset
    if model_photos:
        missing = REQUIRED_MODEL_PHOTOS - set(model_photos.keys())
        if missing:
            return {
                "error": f"Missing model photos: {', '.join(sorted(missing))}. "
                f"Required keys: {', '.join(sorted(REQUIRED_MODEL_PHOTOS))}"
            }
        model_photo_map: dict[str, bytes] = {}
        for name, b64_str in model_photos.items():
            if name not in REQUIRED_MODEL_PHOTOS:
                return {"error": f"Invalid model photo key: '{name}'. Required: {', '.join(sorted(REQUIRED_MODEL_PHOTOS))}"}
            try:
                model_photo_map[name] = base64.b64decode(b64_str)
            except Exception as e:
                return {"error": f"Invalid base64 encoding for model photo '{name}': {e}"}
        logger.info("[product_fitting] Using custom model photos")
    else:
        try:
            model_photo_map = _load_preset_model_photos(ethnicity, gender)
        except ValueError as e:
            return {"error": str(e)}
        logger.info(f"[product_fitting] Using preset model: {ethnicity}_{gender}")

    genai_client, nano_client = _get_clients()

    logger.info(
        f"[MCP product_fitting] Starting: {len(garment_images_bytes)} garments, "
        f"gender={gender}, ethnicity={ethnicity}, max_retries={max_retries}"
    )

    result = await run_fitting_pipeline(
        garment_images_bytes=garment_images_bytes,
        model_photo_map=model_photo_map,
        max_retries=max_retries,
        scenario=scenario,
        generation_model=generation_model,
        gender=gender,
        nano_client=nano_client,
        genai_client=genai_client,
        product_id=product_id or None,
    )

    if result.get("error"):
        return {"error": result["error"]}

    def _format_side(side):
        if side is None:
            return None
        return {
            "image_base64": base64.b64encode(side["image"]).decode("utf-8"),
            "status": side["status"],
            "validation": side["validation"],
            "total_attempts": side.get("total_attempts", 0),
        }

    response = {
        "front": _format_side(result.get("front")),
        "back": _format_side(result.get("back")),
    }
    if result.get("front_skipped_reason"):
        response["front_skipped_reason"] = result["front_skipped_reason"]
    if result.get("back_skipped_reason"):
        response["back_skipped_reason"] = result["back_skipped_reason"]

    logger.info("[MCP product_fitting] Complete")
    return response
