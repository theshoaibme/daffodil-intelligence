from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging
import json

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.user import AgentRequest, AgentResponse
from ..runtime import orchestrator
from ..tools.registry import get_registry
from ..core.config import get_settings

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/test-chat")
async def test_chat(data: dict, user: dict = Depends(get_current_user)):
    message = data.get("message", "")
    user_id = int(user.get("sub"))

    result = await orchestrator.run(message, user_id=user_id)
    return {
        "message": message,
        "detected_agents": result.get("agents") or result.get("tool_calls", []),
        "response": result.get("content", ""),
        "engine": result.get("engine"),
    }


@router.get("/tools")
async def list_tools():
    """List all live tools from the real tool registry."""
    registry = get_registry()
    return {"tools": registry.list_all(), "count": registry.count}


@router.post("/tools/execute")
async def execute_tool(data: dict, user: dict = Depends(get_current_user)):
    """Execute any registered tool by name via the real registry."""
    tool_name = data.get("tool") or data.get("name")
    args = data.get("arguments", {}) or {}
    if not tool_name:
        return {"error": "Missing 'tool' name"}

    registry = get_registry()
    result = await registry.execute(tool_name, **args)
    if result.success:
        return {"success": True, "result": result.data, "duration_ms": result.duration_ms}
    return {"success": False, "error": result.error}


@router.post("/vision/analyze")
async def analyze_vision(data: dict):
    from ..agents.vision import analyze_image
    
    image_data = data.get("image", "")
    
    if not image_data:
        return {"error": "No image provided"}
    
    try:
        result = await analyze_image(image_data)
        return {
            "analysis": result.get("description", "Analyzed successfully"),
            "detected_elements": result.get("detected_elements", []),
            "confidence": result.get("confidence", 0.9)
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/chat", response_model=AgentResponse)
async def chat(
    request: AgentRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    user_id = int(user.get("sub"))
    result = await orchestrator.run(request.message, user_id=user_id)

    return AgentResponse(
        response=result.get("content", ""),
        agent=", ".join(result.get("agents") or [result.get("engine", "main")]),
        tools_used=result.get("tool_calls", []),
        sources=[]
    )


@router.post("/chat/stream")
async def chat_stream(request: AgentRequest, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    logger.info(f"Stream request from user {user_id}: {request.message[:100]}...")

    async def generate():
        try:
            async for token in orchestrator.run_stream(request.message, user_id=user_id):
                if token:
                    yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except asyncio.CancelledError:
            logger.info(f"Stream cancelled for user {user_id}")
            raise
        except Exception as e:
            logger.error(f"Stream error for user {user_id}: {str(e)}")
            yield f"data: [ERROR] An error occurred: {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


async def generate_gemini_stream(prompt: str):
    import httpx
    
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key":
        yield f"data: GEMINI_API_KEY is not configured. Please set it in the .env file.\n\n"
        return
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?key={settings.GEMINI_API_KEY}&alt=sse",
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.9,
                        "maxOutputTokens": 2048,
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        try:
                            data = json.loads(line[5:])
                            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                            for part in parts:
                                if "text" in part:
                                    yield f"data: {part['text']}\n\n"
                        except:
                            pass
            else:
                yield f"data: Error: API returned status {response.status_code}\n\n"
    except Exception as e:
        logger.error(f"Gemini streaming error: {str(e)}")
        yield f"data: Sorry, I encountered an error. Please check your API key configuration.\n\n"


@router.post("/gemini/chat")
async def gemini_chat(data: dict):
    message = data.get("message", "")
    if not message:
        return {"error": "No message provided"}
    
    full_response = ""
    
    async def generate():
        nonlocal full_response
        async for chunk in generate_gemini_stream(message):
            full_response += chunk.replace("data: ", "").replace("\n\n", "")
            yield chunk
        yield f"data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/gemini/chat/simple")
async def gemini_chat_simple(data: dict):
    message = data.get("message", "")
    if not message:
        return {"error": "No message provided"}
    
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key":
        return {
            "error": "GEMINI_API_KEY is not configured. Please set it in the .env file.",
            "source": "config_error"
        }
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}",
                json={
                    "contents": [{
                        "parts": [{"text": f"You are a helpful AI assistant for a university. Answer this query: {message}"}]
                    }],
                    "generationConfig": {
                        "temperature": 0.9,
                        "maxOutputTokens": 2048,
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return {"response": text, "source": "gemini"}
            else:
                return {"error": f"API error: {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}