"""Callbacks for the Document Extraction Agent."""

import base64

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.genai import types
from small_business_loan_agent.shared_libraries.logging_config import get_logger

logger = get_logger(__name__)


def inject_document_into_request(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> None:
    """Before-model callback that injects the inline document into the LLM request.

    When the DocumentExtractionAgent is called as a sub-agent via AgentTool,
    the original multimodal content (PDF/image) is not forwarded. This callback
    reads the document from session state and adds it as an inline_data Part
    so Gemini can natively process it.
    """
    inline_doc = callback_context.state.get("inline_document")
    if not inline_doc or not isinstance(inline_doc, dict):
        logger.warning("No inline_document found in session state")
        return None

    data_b64 = inline_doc.get("data", "")
    mime_type = inline_doc.get("mime_type", "")
    if not data_b64:
        logger.warning("inline_document has empty data")
        return None

    try:
        raw_bytes = base64.b64decode(data_b64)
    except Exception as e:
        logger.error(f"Failed to decode document base64: {e}")
        return None

    doc_part = types.Part(inline_data=types.Blob(mime_type=mime_type, data=raw_bytes))

    # Append the document as a user content entry so the model can see it
    llm_request.contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part(text="Here is the loan application document to extract data from:"),
                doc_part,
            ],
        )
    )

    logger.info(f"Injected document into LLM request: mime_type={mime_type}, size={len(raw_bytes)} bytes")
    return None
