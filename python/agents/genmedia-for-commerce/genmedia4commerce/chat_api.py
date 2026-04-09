import json
import logging
import os
from fastapi import APIRouter, Request, Response, HTTPException, Query
from fastapi.responses import StreamingResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.artifacts.gcs_artifact_service import GcsArtifactService
from google.genai import types as genai_types
from pydantic import BaseModel
from agents.style_advisor_agent.agent import style_advisor_agent, process_text_for_gcs_urls

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize the session service
session_service = InMemorySessionService()

# Initialize Artifact Service
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
if logs_bucket_name:
    artifact_service = GcsArtifactService(bucket_name=logs_bucket_name)
else:
    artifact_service = InMemoryArtifactService()

# Create a runner for the style advisor agent
runner = Runner(
    agent=style_advisor_agent, 
    app_name="style_advisor", 
    session_service=session_service,
    artifact_service=artifact_service
)

class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str

async def chat_streamer(request: ChatRequest):
    # Create the session if it doesn't exist
    if not await session_service.get_session(
        app_name="style_advisor", user_id=request.user_id, session_id=request.session_id
    ):
        await session_service.create_session(
            app_name="style_advisor", user_id=request.user_id, session_id=request.session_id
        )

    # Stream the response from the agent
    async for event in runner.run_async(
        user_id=request.user_id,
        session_id=request.session_id,
        new_message=genai_types.Content(
            role="user", parts=[genai_types.Part.from_text(text=request.message)]
        ),
    ):
        # 1. Check for Tool Responses (Product Data)
        if event.get_function_responses():
            for response in event.get_function_responses():
                # Handling specialized product JSON if available
                if isinstance(response.response, dict) and "content" in response.response:
                    content_list = response.response["content"]
                    if isinstance(content_list, list) and len(content_list) > 0:
                        for item in content_list:
                            if item.get("type") == "text" and "text" in item:
                                try:
                                    # Process inner JSON to replace GCS URLs before converting to object
                                    processed_text = await process_text_for_gcs_urls(
                                        item["text"], 
                                        runner, 
                                        user_id=request.user_id, 
                                        session_id=request.session_id
                                    )
                                    products_data = json.loads(processed_text)
                                    if isinstance(products_data, list):
                                        yield json.dumps({"type": "products", "content": products_data}) + "\n"
                                except Exception:
                                    # DO NOT yield raw text from tools to the user
                                    pass

        # 2. Check for Final Text Response
        if event.is_final_response() and event.content and event.content.parts:
             for part in event.content.parts:
                 if part.text:
                     # Process final text for GCS URLs before yielding
                     processed_text = await process_text_for_gcs_urls(
                         part.text, 
                         runner, 
                         user_id=request.user_id, 
                         session_id=request.session_id
                     )
                     yield json.dumps({"type": "text", "content": processed_text}) + "\n"

@router.post("/chat")
async def chat(request: Request):
    chat_request_data = await request.json()
    return StreamingResponse(
        chat_streamer(ChatRequest(**chat_request_data)), media_type="text/event-stream"
    )

@router.get("/api/artifacts/{artifact_name}")
async def get_artifact(
    artifact_name: str,
    app: str = Query(...),
    user: str = Query(...),
    session: str = Query(...),
):
    try:
        artifact = await artifact_service.load_artifact(
            app_name=app,
            user_id=user,
            session_id=session,
            filename=artifact_name,
        )
        if not artifact or not artifact.inline_data:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        data = artifact.inline_data.data
        if isinstance(data, str): # Handle base64 encoded strings
            import base64
            data = base64.b64decode(data)
            
        return Response(
            content=data,
            media_type=artifact.inline_data.mime_type or "image/png"
        )
    except Exception as e:
        logger.error(f"Error loading artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))
