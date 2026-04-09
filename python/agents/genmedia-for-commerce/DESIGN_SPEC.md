# DESIGN_SPEC.md

## Overview

GenMedia for Commerce is a generative AI platform for creating marketing media for retail products. The system uses an ADK-based agent architecture with MCP tools.

Each media generation workflow (image VTO, video VTO, spinning videos, background changer, product fitting) is exposed as an MCP tool. An ADK root agent routes natural-language user requests to the appropriate tool. The React frontend works via REST API endpoints, while the MCP tools are also callable standalone or by external agents.

## Example Use Cases

1. **Natural language routing**: User says "Generate a product fitting for these garment images on a female model" → Agent calls `product_fitting` MCP tool with the right parameters.

2. **Direct MCP tool call**: External system calls the `product_fitting` tool directly via MCP protocol with base64 garment images, gender, and ethnicity.

3. **Frontend compatibility**: React frontend calls REST endpoints (e.g., `/api/product-enrichment/product-fitting/generate-fitting-pipeline`).

4. **Multi-workflow orchestration**: User says "First generate a product fitting, then create a video VTO from the result" → Agent chains `product_fitting` → `video_vto_clothes` tools.

5. **Standalone MCP server**: The MCP server runs independently via `python -m mcp_server.server` for integration with any MCP client.

## Implemented Tools

| Tool | Description |
|------|-------------|
| `product_fitting` | B2B catalogue enrichment: single garment on AI model body (front/back) |
| `image_vto_clothes` | B2C virtual try-on: real person wearing multiple garments (images) |
| `glasses_vto` | B2C virtual try-on: real person wearing glasses (images) |
| `glasses_enhance` | Enhance glasses VTO images |
| `glasses_edit_frame` | Edit glasses frame style |
| `video_vto_clothes` | B2C virtual try-on: real person wearing garments (video) |
| `glasses_video_generate` | B2C virtual try-on: real person wearing glasses (video) |
| `glasses_video_regenerate` | Regenerate glasses videos |
| `background_changer` | Background replacement |
| `spinning_shoes_r2v` | 360° shoe spinning videos (R2V) |
| `spinning_other_r2v` | Generic product R2V spinning |
| `spinning_interpolation` | Frame interpolation spinning videos |
| `catalog_search` | Search product catalog by text/image similarity |

## Architecture

Every workflow is accessible in three ways:

```
Frontend (React)  ───→  REST API endpoints (FastAPI routers: *_api.py)
External Agents   ───→  MCP Server (SSE transport, port 8081)
ADK Playground    ───→  ADK Agent → MCP tools (stdio transport)
```

```
genmedia4commerce/
├── agents/
│   ├── router_agent/              → Routes NL requests to MCP tools
│   └── style_advisor_agent/       → Fashion search + outfit curation
├── mcp_server/
│   ├── server.py                  → MCP server (stdio + SSE transport)
│   └── <workflow>/                → *_mcp.py (MCP tool) + *_api.py (REST router)
├── workflows/
│   └── <workflow>/                → Pipeline/business logic
├── fast_api_app.py                → Combined app for Cloud Run (ADK + REST + MCP + frontend)
├── agent_engine_app.py            → Agent Engine entrypoint (Vertex AI managed deployment)
├── frontend/                      → Production React frontend
└── frontend_dev/                  → Dev React frontend
```

## Agents

### Router Agent

The root ADK agent (`agents/router_agent/`) routes natural-language requests to the appropriate MCP tool. It handles:
- Image uploads (extracts base64 from user messages)
- Reference resolution (e.g., "use the previous fitting result")
- Result extraction as artifacts (images, videos)
- Multi-workflow orchestration (chaining tools)

### Style Advisor Agent

A fashion curation agent (`agents/style_advisor_agent/`) with two sub-agents:

1. **Style Advisor (Searcher)**: Takes a user request (e.g., "outfit for a beach wedding"), searches the product catalog across categories using `catalog_search`, then delegates to the curator.
2. **Stylish (Curator)**: Receives search results, curates 3 complete outfit looks with descriptions and product images.

Uses `McpToolset` for catalog searches and Google Search for trend inspiration. Model: `gemini-3-flash-preview`.

## Catalog Search

In-memory product search powered by pre-computed embeddings:

- **61,786 fashion products** with descriptions, images, categories, and attributes
- **Embeddings**: Pre-computed with `gemini-embedding-001`, stored as `embeddings.npy` (float32, 724 MB)
- **Metadata**: Product attributes stored as `metadata.parquet` (23 MB)
- **Search**: Numpy dot-product similarity, ~42ms per query over all products
- **Loading**: Auto-downloaded from GCS at startup via `config.py`, stored in `assets/backend_assets/catalogue/`
- **GCS Bucket**: Computed at runtime from a seed hash (not hardcoded)

The catalog loads eagerly at import time (`_load()` at module level in `vector_search.py`), ensuring data is ready before the first request.

## Shoe Classifier

The shoes spinning pipeline requires a shoe angle classifier to determine image orientation (front, back, left, right, etc.).

### Baseline (no setup)
Uses Gemini multimodal embeddings + a numpy neural network. Works out of the box when `SHOE_CLASSIFICATION_ENDPOINT=None` in `config.env`.

### Fine-tuned Gemini LoRA (better accuracy)
1. `make train-shoe-model` — Fine-tune Gemini 2.5 Flash with LoRA for shoe classification
2. `make eval-set-shoe-model` — Evaluate all endpoints on the test set, auto-update `config.env` with the best endpoint

Training parameters are configurable via environment variables: `FINETUNE_EPOCHS`, `FINETUNE_LORA_RANK`, `FINETUNE_LR_MULTIPLIER`, `FINETUNE_VERSION`, `FINETUNE_BASE_MODEL`.

## Constraints & Safety Rules

- The agent must NOT modify or delete any user-uploaded images.
- The agent must NOT change model parameters (model name, temperature, etc.) unless explicitly requested.
- All image data is transmitted as base64 — no file paths exposed to the agent.
- The agent should clearly report generation failures rather than silently retrying indefinitely.
- The MCP server must validate all inputs before calling pipeline functions.

## Success Criteria

- All MCP tools produce results consistent with the REST endpoints.
- ADK agent correctly routes requests to the appropriate tool.
- Frontend remains fully functional via REST API.
- MCP server can be run standalone and called by external MCP clients.
- `make playground` launches the ADK agent with working tool access.
