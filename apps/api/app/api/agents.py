from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.user import AgentRequest, AgentResponse
from ..agents.supervisor import detect_intent, process_with_agents, synthesize_response
from ..graph.orchestrator import di_graph
import logging

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)


@router.post("/test-chat")
async def test_chat(data: dict):
    message = data.get("message", "")
    from ..agents.supervisor import detect_intent, process_with_agents, synthesize_response
    
    agents = detect_intent(message)
    results = await process_with_agents(message, agents, {"user_id": 1})
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
    import base64
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

    async def generate():
        async for event in di_graph.astream({
            "message": request.message,
            "user_id": user_id
        }):
            if "synthesize" in event:
                yield f"data: {event['synthesize'].get('final_response', '')}\n\n"

    return generate()