import asyncio
import base64
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from google.cloud import storage
from google.genai import types

from genmedia4commerce.config import MEDIA_BUCKET, _ASSET_BUCKET, genai_client
from genmedia4commerce.workflows.shared.gcs_utils import upload_bytes_to_gcs
from genmedia4commerce.workflows.shared.llm_utils import get_generate_content_config, get_part

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)


def _session_prefix(global_session_id: str) -> str:
    return f"sessions/{global_session_id}"


def _history_blob_path(global_session_id: str) -> str:
    return f"{_session_prefix(global_session_id)}/history.json"


def user_upload_path(global_session_id: str, filename: str) -> str:
    return f"{_session_prefix(global_session_id)}/user_uploads/{filename}"


def generated_asset_path(global_session_id: str, filename: str) -> str:
    return f"{_session_prefix(global_session_id)}/generated_assets/{filename}"


def retrieve_from_history(global_session_id: str) -> list[types.Content]:
    """Load conversation history from GCS for the given session.

    Returns an empty list if the session file doesn't exist yet.
    """
    blob_path = _history_blob_path(global_session_id)
    try:
        client = storage.Client()
        bucket = client.bucket(MEDIA_BUCKET)
        blob = bucket.blob(blob_path)
        if not blob.exists():
            return []
        raw = json.loads(blob.download_as_text())
        return [types.Content.model_validate(entry) for entry in raw]
    except Exception as e:
        logger.warning(f"Failed to retrieve history for {global_session_id}: {e}")
        return []


def append_to_history(global_session_id: str, data) -> None:
    """Append a Content or LlmResponse to the GCS-backed conversation history.

    Args:
        global_session_id: The stable session UUID.
        data: A types.Content, or an LlmResponse (has .content attribute).
    """
    if hasattr(data, "content"):
        content = data.content
    else:
        content = data

    if content is None:
        return

    history = retrieve_from_history(global_session_id)
    history.append(content)

    blob_path = _history_blob_path(global_session_id)
    try:
        serialized = json.dumps(
            [entry.model_dump(mode="json", exclude_none=True) for entry in history],
        )
        upload_bytes_to_gcs(
            MEDIA_BUCKET,
            serialized.encode("utf-8"),
            blob_path,
            content_type="application/json",
        )
        logger.info(
            f"Appended to history gs://{MEDIA_BUCKET}/{blob_path} "
            f"({len(history)} entries)"
        )
    except Exception as e:
        logger.warning(f"Failed to append to history for {global_session_id}: {e}")


async def upload_asset_to_gcs(
    data: bytes, blob_path: str, content_type: str,
    bucket: str = MEDIA_BUCKET, project_id: str = None,
) -> Optional[str]:
    """Upload an asset to GCS.

    Args:
        data: The file bytes.
        blob_path: Full blob path within the bucket.
        content_type: The content type of the file.
        bucket: GCS bucket name. Defaults to MEDIA_BUCKET.
        project_id: The project ID.

    Returns:
        The GCS URI if successful, None otherwise.
    """
    try:

        def _upload():
            upload_bytes_to_gcs(
                bucket,
                data,
                blob_path,
                content_type=content_type,
                project_id=project_id,
            )

        await asyncio.get_event_loop().run_in_executor(None, _upload)
        return f"gs://{bucket}/{blob_path}"
    except Exception as e:
        logger.warning(f"Failed to upload asset to GCS: {e}")
        return None


async def copy_gcs_asset(
    source_uri: str, dest_blob_path: str, dest_bucket: str = MEDIA_BUCKET,
) -> Optional[str]:
    """Copy a GCS object to a new location without downloading.

    Args:
        source_uri: Full gs:// URI of the source object.
        dest_blob_path: Destination blob path within dest_bucket.
        dest_bucket: Destination bucket name. Defaults to MEDIA_BUCKET.

    Returns:
        The destination GCS URI if successful, None otherwise.
    """
    src_path = source_uri[len("gs://"):]
    src_bucket_name, src_blob_name = src_path.split("/", 1)

    def _copy():
        client = storage.Client()
        src_bucket = client.bucket(src_bucket_name)
        src_blob = src_bucket.blob(src_blob_name)
        dst_bucket = client.bucket(dest_bucket)
        src_bucket.copy_blob(src_blob, dst_bucket, dest_blob_path)

    try:
        await asyncio.get_event_loop().run_in_executor(None, _copy)
        return f"gs://{dest_bucket}/{dest_blob_path}"
    except Exception as e:
        logger.warning(f"Failed to copy {source_uri} → gs://{dest_bucket}/{dest_blob_path}: {e}")
        return None


def extract_media(parsed, tool_name: str) -> list[bytes | str]:
    """Extract all media references from a parsed tool result.

    Walks the object and collects:
    - base64-encoded strings (keys ending in '_base64') → decoded to bytes
    - gs:// URIs (from 'img_path' fields) → kept as str for later download

    Returns an ordered list of bytes | str.
    """
    media: list[bytes | str] = []

    def _walk_dict(d: dict, depth: int = 0):
        if depth > 3:
            return
        for k, v in d.items():
            if k.endswith("_base64"):
                if isinstance(v, str) and len(v) > 1000:
                    try:
                        media.append(base64.b64decode(v))
                    except Exception:
                        pass
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and len(item) > 1000:
                            try:
                                media.append(base64.b64decode(item))
                            except Exception:
                                pass
            elif k == "img_path" and isinstance(v, str) and v.startswith("gs://"):
                media.append(v)
            elif isinstance(v, dict):
                _walk_dict(v, depth + 1)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        _walk_dict(item, depth + 1)

    if isinstance(parsed, dict):
        _walk_dict(parsed)
    elif isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                _walk_dict(item)

    return media


def resolve_filename_to_gcs_uri(filename: str, global_session_id: str) -> str:
    """Reconstruct a GCS URI from a filename based on naming convention.

    Filenames follow the pattern: {timestamp}_{type}_{i}.{ext}
    - _u_ → user upload → session user_uploads folder (MEDIA_BUCKET)
    - _c_ → catalog item → session generated_assets folder (MEDIA_BUCKET)
    - _g_ → generated asset → session generated_assets folder (MEDIA_BUCKET)
    """
    parts = filename.split("_")
    if len(parts) >= 3:
        file_type = parts[1]
        if file_type == "u":
            return f"gs://{MEDIA_BUCKET}/{user_upload_path(global_session_id, filename)}"
        elif file_type in ("c", "g"):
            return f"gs://{MEDIA_BUCKET}/{generated_asset_path(global_session_id, filename)}"
    return f"gs://{_ASSET_BUCKET}/{filename}"


def describe_input_attachment(img_bytes: bytes, conversation_context: str) -> str:
    """Generate a short contextual description of an uploaded image.

    Uses the conversation context to understand what type of attachment this is.
    """
    config = get_generate_content_config(
        temperature=0,
        thinking_budget=0,
        response_mime_type="text/plain",
    )
    prompt = (
        f"This is the conversation context so far:\n{conversation_context}\n\n"
        "The user just uploaded this image. Describe it in one detailed sentence. "
        "If it's a person, mention gender, pose, visible clothing, and setting. "
        "If it's a garment or product, mention the type (shirt, dress, shoes, sunglasses...), "
        "color, pattern, brand/logo if visible, material, and any distinctive details "
        "(e.g. 'white Nike sneakers with red swoosh and chunky sole'). "
        "Be specific enough that someone could distinguish this item from similar ones."
    )
    parts = [get_part(prompt), get_part(img_bytes)]
    contents = [types.Content(role="user", parts=parts)]
    result = genai_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=contents,
        config=config,
    )
    return result.candidates[0].content.parts[0].text.strip()


def describe_input_attachments_parallel(
    attachments: list[bytes], conversation_context: str
) -> list[str]:
    """Describe multiple attachments in parallel."""
    if not attachments:
        return []

    with ThreadPoolExecutor(max_workers=len(attachments)) as executor:
        futures = [
            executor.submit(describe_input_attachment, img, conversation_context)
            for img in attachments
        ]
        return [f.result() for f in futures]


def _download_from_gcs(gcs_uri: str) -> bytes | None:
    """Download raw bytes from a gs:// URI."""
    path = gcs_uri[len("gs://"):]
    bucket_name, blob_name = path.split("/", 1)
    try:
        client = storage.Client()
        return client.bucket(bucket_name).blob(blob_name).download_as_bytes()
    except Exception as e:
        logger.warning(f"Failed to download {gcs_uri}: {e}")
        return None


async def resolve_media(media: list[bytes | str]) -> list[bytes]:
    """Resolve a mixed list of bytes and gs:// URIs into all bytes.

    Downloads GCS URIs in parallel. Drops any failed downloads.
    """
    loop = asyncio.get_event_loop()
    resolved: list[bytes] = []

    # Collect indices that need downloading
    download_tasks = []
    for i, item in enumerate(media):
        if isinstance(item, str):
            download_tasks.append((i, item))

    # Download in parallel
    downloads: dict[int, bytes | None] = {}
    if download_tasks:
        results = await asyncio.gather(*[
            loop.run_in_executor(None, _download_from_gcs, uri)
            for _, uri in download_tasks
        ])
        for (i, _), data in zip(download_tasks, results):
            downloads[i] = data

    # Merge in order
    for i, item in enumerate(media):
        if isinstance(item, bytes):
            resolved.append(item)
        elif i in downloads and downloads[i] is not None:
            resolved.append(downloads[i])

    return resolved
