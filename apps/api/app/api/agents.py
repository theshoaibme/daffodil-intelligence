from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging
import json

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.user import AgentRequest, AgentResponse
from ..agents.supervisor import detect_intent, process_with_agents, synthesize_response
from ..graph.orchestrator import di_graph
from ..core.config import get_settings

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/test-chat")
async def test_chat(data: dict, user: dict = Depends(get_current_user)):
    message = data.get("message", "")
    user_id = int(user.get("sub"))
    
    agents = detect_intent(message)
    results = await process_with_agents(message, agents, {"user_id": user_id})
    response = await synthesize_response(results, message)
    
    return {
        "message": message,
        "detected_agents": agents,
        "response": response
    }


@router.get("/tools")
async def list_tools():
    from ..mcp.client import TOOL_REGISTRY
    return {"tools": list(TOOL_REGISTRY.keys()), "count": len(TOOL_REGISTRY)}


@router.post("/tools/execute")
async def execute_tool(data: dict):
    from ..mcp.client import TOOL_REGISTRY
    from ..core.university_data import university_data
    
    tool_name = data.get("tool")
    args = data.get("arguments", {})
    
    if tool_name == "get_cgpa":
        result = await university_data.get_cgpa(args.get("user_id", "STU00001"))
        return {"result": result}
    elif tool_name == "search_books":
        result = await university_data.search_books(args.get("query", ""))
        return {"result": result}
    elif tool_name == "get_shuttle_schedule":
        result = await university_data.get_shuttle_schedule()
        return {"result": result}
    elif tool_name == "get_jobs":
        result = await university_data.get_jobs(args.get("query"))
        return {"result": result}
    else:
        return {"error": "Tool not found"}


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
    agents = detect_intent(request.message)
    results = await process_with_agents(request.message, agents, {"user_id": user_id})
    response = await synthesize_response(results, request.message)

    return AgentResponse(
        response=response,
        agent=", ".join(agents),
        tools_used=[],
        sources=[]
    )


@router.post("/chat/stream")
async def chat_stream(request: AgentRequest, user: dict = Depends(get_current_user)):
    user_id = int(user.get("sub"))
    agents = detect_intent(request.message)
    logger.info(f"Stream request from user {user_id}: {request.message[:100]}...")

    async def generate():
        try:
            async for event in di_graph.astream({
                "message": request.message,
                "user_id": user_id,
                "agents": agents
            }):
                if "synthesize" in event:
                    response_text = event['synthesize'].get('final_response', '')
                    if response_text:
                        yield f"data: {response_text}\n\n"
                elif "error" in event:
                    yield f"data: [ERROR] {event['error']}\n\n"
                    break
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
        mock_responses = [
            "Hello! I'm your AI assistant. How can I help you today?",
            "I can help you with your academic queries, library searches, campus information, and more!",
            "Try asking me about your CGPA, available books, shuttle schedules, or career opportunities.",
        ]
        for response in mock_responses:
            yield f"data: {response}\n\n"
            await asyncio.sleep(0.5)
        return
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:streamGenerateContent?key={settings.GEMINI_API_KEY}&alt=sse",
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
            "response": "Hello! I'm your AI assistant powered by Gemini. Please configure your GEMINI_API_KEY in the .env file to enable full functionality. For now, I can help with basic queries about your university - try asking about CGPA, library books, or campus shuttle!",
            "source": "mock"
        }
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={settings.GEMINI_API_KEY}",
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