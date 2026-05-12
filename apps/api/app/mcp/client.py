import httpx
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_tools(self) -> List[Dict]:
        try:
            response = await self.client.get(f"{self.base_url}/tools")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get tools: {e}")
            return []

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict:
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/execute",
                json={"name": tool_name, "arguments": arguments}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name}: {e}")
            return {"error": str(e)}

    async def close(self):
        await self.client.aclose()


mcp_client = MCPClient()


TOOL_REGISTRY = {
    # Academic Tools
    "get_cgpa": {"description": "Get student's current CGPA", "params": ["user_id"]},
    "get_courses": {"description": "Get courses for a semester", "params": ["semester"]},
    "get_results": {"description": "Get academic results", "params": ["user_id", "semester"]},
    "get_exam_schedule": {"description": "Get exam schedule", "params": ["student_id", "semester"]},
    "get_attendance": {"description": "Get attendance records", "params": ["student_id", "course_code"]},
    "get_academic_calendar": {"description": "Get academic calendar", "params": []},
    "calculate_gpa": {"description": "Calculate GPA from grades", "params": ["grades"]},
    
    # Library Tools
    "search_books": {"description": "Search library books", "params": ["query"]},
    "check_availability": {"description": "Check book availability", "params": ["book_title"]},
    "get_journals": {"description": "Get academic journals", "params": ["topic"]},
    "reserve_book": {"description": "Reserve a book", "params": ["book_id", "student_id"]},
    
    # Transport Tools
    "get_shuttle_schedule": {"description": "Get shuttle schedule", "params": ["route"]},
    "get_shuttle_location": {"description": "Get current shuttle location", "params": ["route"]},
    "track_shuttle": {"description": "Track shuttle live", "params": ["route"]},
    "get_routes": {"description": "Get all transport routes", "params": []},
    "book_vehicle": {"description": "Book a vehicle", "params": ["vehicle_type", "destination", "date"]},
    
    # Campus Tools
    "get_notices": {"description": "Get campus notices", "params": []},
    "get_events": {"description": "Get upcoming events", "params": ["category"]},
    "register_event": {"description": "Register for an event", "params": ["event_id", "student_id"]},
    "join_club": {"description": "Join a student club", "params": ["club_name", "student_id"]},
    
    # Career Tools
    "search_jobs": {"description": "Search job opportunities", "params": ["query"]},
    "get_internships": {"description": "Get internships", "params": ["query"]},
    "review_cv": {"description": "Review CV/resume", "params": ["cv_text"]},
    "generate_roadmap": {"description": "Generate career roadmap", "params": ["role", "current_level"]},
    "mock_interview": {"description": "Practice interview", "params": ["position"]},
    
    # Hostel Tools
    "book_hostel": {"description": "Book hostel room", "params": ["student_id", "preferences"]},
    "get_hostel_info": {"description": "Get hostel information", "params": ["student_id"]},
    "submit_hostel_complaint": {"description": "Submit hostel complaint", "params": ["student_id", "issue"]},
    "get_hostel_facilities": {"description": "Get hostel facilities", "params": ["building"]},
    
    # Fee & Finance Tools
    "calculate_fee": {"description": "Calculate tuition fee", "params": ["student_id", "semester"]},
    "get_payment_status": {"description": "Get payment status", "params": ["student_id"]},
    "get_scholarships": {"description": "Get available scholarships", "params": []},
    "apply_waiver": {"description": "Apply for waiver", "params": ["student_id", "waiver_type"]},
    "get_installment_info": {"description": "Get installment options", "params": ["student_id"]},
    
    # Complaint Tools
    "submit_complaint": {"description": "Submit a complaint", "params": ["category", "description", "student_id"]},
    "get_complaint_status": {"description": "Get complaint status", "params": ["complaint_id"]},
    "escalate_issue": {"description": "Escalate an issue", "params": ["complaint_id", "reason"]},
    "give_feedback": {"description": "Submit feedback", "params": ["category", "rating", "comment"]},
    
    # Notification Tools
    "get_notifications": {"description": "Get user notifications", "params": ["user_id", "limit"]},
    "send_notification": {"description": "Send notification", "params": ["user_id", "title", "message"]},
    "mark_notification_read": {"description": "Mark notification as read", "params": ["notification_id"]},
    "set_notification_preferences": {"description": "Set notification preferences", "params": ["user_id", "preferences"]},
    
    # Research Tools
    "search_papers": {"description": "Search research papers", "params": ["query"]},
    "help_thesis": {"description": "Get thesis help", "params": ["topic"]},
    "generate_abstract": {"description": "Generate paper abstract", "params": ["topic"]},
    
    # Development Tools
    "debug_code": {"description": "Debug code errors", "params": ["code", "error"]},
    "explain_code": {"description": "Explain code", "params": ["code"]},
    "generate_code": {"description": "Generate code", "params": ["language", "task"]},
    
    # AI Tools
    "analyze_image": {"description": "Analyze an image", "params": ["image_data"]},
    "read_pdf": {"description": "Read PDF content", "params": ["file_path"]},
    "transcribe_audio": {"description": "Transcribe audio", "params": ["audio_data"]},
}


async def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    if tool_name in TOOL_REGISTRY:
        return await mcp_client.execute_tool(tool_name, kwargs)
    return {"error": f"Unknown tool: {tool_name}"}