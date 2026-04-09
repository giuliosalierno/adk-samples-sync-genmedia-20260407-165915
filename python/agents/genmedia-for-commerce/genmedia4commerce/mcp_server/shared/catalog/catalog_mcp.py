"""MCP tool wrapper for catalog search."""

import asyncio
import logging

from workflows.shared.vector_search import search

logger = logging.getLogger(__name__)


async def run_catalog_search(
    query: str,
    k: int = 12,
    audience: str | None = None,
) -> dict:
    """Search the product catalog for items matching a text query.

    Uses vector similarity search to find products matching the description.

    Args:
        query: Text description of what to search for
            (e.g. "red casual dress", "blue running shoes").
        k: Number of results to return. Default: 12.
        audience: Optional filter for target audience. Accepted values:
            "women", "men", "unisex", or a comma-separated combination
            (e.g. "men,unisex"). If not specified, searches all audiences.

    Returns:
        Dictionary with 'results' list containing matched products
        with description, image URL, category, color, style, audience, and score.
    """
    filters = None
    if audience:
        filters = {"audience": [a.strip() for a in audience.split(",")]}

    logger.info(f"[MCP catalog_search] Query: {query}, k={k}, filters={filters}")

    loop = asyncio.get_event_loop()

    try:
        results = await loop.run_in_executor(
            None, lambda: search(query, k=k, filters=filters)
        )
    except Exception as e:
        logger.error(f"[MCP catalog_search] Search failed: {e}")
        return {"results": [], "error": str(e)}

    def _format_results(results):
        return [item.get("data", {}) for item in results]

    logger.info(f"[MCP catalog_search] Complete. {len(results)} results")
    return {"results": _format_results(results)}
