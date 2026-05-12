"""
Daffodil Intelligence - MCP Tool Server
Model Context Protocol Implementation
"""

import asyncio
import json
import time
import hashlib
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class ToolCategory(Enum):
    ACADEMIC = "academic"
    LIBRARY = "library"
    CAMPUS = "campus"
    CAREER = "career"
    FINANCE = "finance"
    VISION = "vision"
    VOICE = "voice"
    REALTIME = "realtime"
    SYSTEM = "system"


class Permission(Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"
    PUBLIC = "public"


@dataclass
class ToolDefinition:
    name: str
    description: str
    category: ToolCategory
    input_schema: Dict
    permissions: List[Permission]
    realtime: bool = False
    cache_ttl: int = 60
    execute: Optional[Callable] = None
    rate_limit: int = 100  # requests per minute


@dataclass
class ToolRequest:
    tool_name: str
    parameters: Dict
    user_id: Optional[str] = None
    role: str = "student"
    session_id: Optional[str] = None


@dataclass
class ToolResponse:
    success: bool
    tool: str
    data: Any = None
    error: Optional[str] = None
    latency_ms: float = 0
    source: str = "cache"
    cached: bool = False


@dataclass
class ExecutionContext:
    user_id: Optional[str]
    role: str
    session_id: str
    start_time: float
    request_id: str


# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.lock = asyncio.Lock()
    
    async def check_limit(self, key: str, limit: int, window: int = 60) -> bool:
        async with self.lock:
            now = time.time()
            if key not in self.requests:
                self.requests[key] = []
            
            # Remove old requests
            self.requests[key] = [t for t in self.requests[key] if now - t < window]
            
            if len(self.requests[key]) >= limit:
                return False
            
            self.requests[key].append(now)
            return True


# ============================================================================
# INPUT SANITIZER
# ============================================================================

class InputSanitizer:
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
        
        # Trim to max length
        return value[:max_length].strip()
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return email.lower()
        raise ValueError("Invalid email format")
    
    @staticmethod
    def sanitize_integer(value: Any, min_val: int = None, max_val: int = None) -> int:
        try:
            result = int(value)
            if min_val is not None and result < min_val:
                raise ValueError(f"Value below minimum: {min_val}")
            if max_val is not None and result > max_val:
                raise ValueError(f"Value above maximum: {max_val}")
            return result
        except (ValueError, TypeError):
            raise ValueError("Invalid integer")
    
    @staticmethod
    def sanitize_dict(value: Dict, allowed_keys: List[str] = None) -> Dict:
        if not isinstance(value, dict):
            raise ValueError("Invalid dict")
        
        if allowed_keys:
            return {k: v for k, v in value.items() if k in allowed_keys}
        return value


# ============================================================================
# CACHE SYSTEM
# ============================================================================

class ToolCache:
    def __init__(self):
        self.cache: Dict[str, tuple] = {}  # key -> (data, expiry)
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self.lock:
            if key in self.cache:
                data, expiry = self.cache[key]
                if time.time() < expiry:
                    return data
                del self.cache[key]
        return None
    
    async def set(self, key: str, data: Any, ttl: int):
        async with self.lock:
            self.cache[key] = (data, time.time() + ttl)
    
    async def invalidate(self, pattern: str = None):
        async with self.lock:
            if pattern:
                self.cache = {k: v for k, v in self.cache.items() if not k.startswith(pattern)}
            else:
                self.cache.clear()


# ============================================================================
# TOOL REGISTRY
# ============================================================================

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.category_index: Dict[ToolCategory, List[str]] = {}
    
    def register(self, tool: ToolDefinition):
        self.tools[tool.name] = tool
        
        if tool.category not in self.category_index:
            self.category_index[tool.category] = []
        self.category_index[tool.category].append(tool.name)
        
        logger.info(f"Registered tool: {tool.name}")
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        return self.tools.get(name)
    
    def list_tools(self, category: ToolCategory = None, permissions: List[Permission] = None) -> List[ToolDefinition]:
        results = []
        
        for tool in self.tools.values():
            if category and tool.category != category:
                continue
            if permissions and not any(p in tool.permissions for p in permissions):
                continue
            results.append(tool)
        
        return results
    
    def get_schema(self) -> Dict:
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "category": t.category.value,
                    "input_schema": t.input_schema,
                    "permissions": [p.value for p in t.permissions],
                    "realtime": t.realtime
                }
                for t in self.tools.values()
            ]
        }


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

class AcademicTools:
    @staticmethod
    async def get_cgpa(user_id: str) -> Dict:
        # Mock CGPA calculation
        return {
            "cgpa": 3.75,
            "total_credits": 90,
            "semester": "Spring 2024",
            "grade_distribution": {"A": 15, "B": 8, "C": 2},
            "trend": [3.5, 3.6, 3.7, 3.75]
        }
    
    @staticmethod
    async def get_courses(semester: int) -> List[Dict]:
        courses = [
            {"code": "CS301", "name": "Algorithms", "credits": 3, "grade": "A"},
            {"code": "CS302", "name": "Database Systems", "credits": 3, "grade": "A-"},
            {"code": "CS303", "name": "Computer Networks", "credits": 3, "grade": "B+"},
            {"code": "CS304", "name": "Software Engineering", "credits": 3, "grade": "A"},
        ]
        return courses
    
    @staticmethod
    async def get_results(user_id: str, semester: int = None) -> Dict:
        return {
            "semester": "Spring 2024",
            "gpa": 3.85,
            "courses": [
                {"code": "CS301", "name": "Algorithms", "grade": "A", "grade_point": 4.0},
                {"code": "CS302", "name": "Database Systems", "grade": "A-", "grade_point": 3.7},
            ]
        }
    
    @staticmethod
    async def check_prerequisites(course_code: str) -> Dict:
        prereqs = {
            "CS301": ["CS201", "CS202"],
            "CS302": ["CS201"],
            "CS401": ["CS301", "CS302"],
        }
        return {"prerequisites": prereqs.get(course_code, []), "completed": True}


class LibraryTools:
    @staticmethod
    async def search_books(query: str, limit: int = 10) -> List[Dict]:
        books = [
            {"title": "Introduction to Algorithms", "author": "Cormen", "available": 3, "location": "CS Section"},
            {"title": "Clean Code", "author": "Martin", "available": 5, "location": "CS Section"},
            {"title": "Design Patterns", "author": "Gang of Four", "available": 2, "location": "CS Section"},
            {"title": "Machine Learning", "author": "Tom Mitchell", "available": 4, "location": "AI Section"},
        ]
        return [b for b in books if query.lower() in b["title"].lower()][:limit]
    
    @staticmethod
    async def check_availability(book_title: str) -> Dict:
        return {"available": 3, "location": "CS Section", "due_date": None}
    
    @staticmethod
    async def get_seat_availability() -> Dict:
        return {"total_seats": 200, "available": 45, "floor_wise": {"1": 10, "2": 15, "3": 20}}


class CampusTools:
    @staticmethod
    async def get_shuttle_schedule() -> List[Dict]:
        return [
            {"route": "Main Gate - Academic Building", "next_arrival": "5 mins", "status": "On Time"},
            {"route": "Hostel - Library", "next_arrival": "12 mins", "status": "On Time"},
        ]
    
    @staticmethod
    async def get_shuttle_location(route: str) -> Dict:
        return {"current_stop": "Academic Building", "eta": "3 mins", "latitude": 23.985, "longitude": 90.402}
    
    @staticmethod
    async def get_notices(category: str = None) -> List[Dict]:
        notices = [
            {"title": "Midterm Exam Schedule", "date": "2024-03-15", "priority": "high", "category": "academic"},
            {"title": "Library Holiday Notice", "date": "2024-03-20", "priority": "medium", "category": "library"},
            {"title": "Career Fair", "date": "2024-03-25", "priority": "low", "category": "career"},
        ]
        if category:
            return [n for n in notices if n["category"] == category]
        return notices
    
    @staticmethod
    async def get_classroom_availability(room: str = None) -> Dict:
        return {
            "rooms": [
                {"room": "101", "building": "A", "available": True, "next_available": "10:00"},
                {"room": "102", "building": "A", "available": False, "occupied_until": "12:00"},
            ]
        }


class CareerTools:
    @staticmethod
    async def search_jobs(query: str, limit: int = 10) -> List[Dict]:
        jobs = [
            {"title": "Software Engineer Intern", "company": "TechCorp", "location": "Remote", "deadline": "2024-04-01"},
            {"title": "Frontend Developer", "company": "WebStudio", "location": "Dhaka", "deadline": "2024-03-25"},
        ]
        return jobs[:limit]
    
    @staticmethod
    async def analyze_cv(cv_text: str) -> Dict:
        return {
            "score": 85,
            "strengths": ["Clear structure", "Relevant experience", "Good keywords"],
            "improvements": ["Add more metrics", "Include skills section"],
            "ats_score": 78
        }
    
    @staticmethod
    async def generate_roadmap(role: str, current_level: str) -> List[Dict]:
        return [
            {"step": 1, "action": "Master fundamentals", "timeline": "3 months"},
            {"step": 2, "action": "Build projects", "timeline": "6 months"},
            {"step": 3, "action": "Apply for internships", "timeline": "9 months"},
        ]


class FinanceTools:
    @staticmethod
    async def get_tuition_fees(semester: int = 1) -> Dict:
        return {
            "per_credit": 5000,
            "total_credits": 15,
            "tuition": 75000,
            "lab_fees": 2000,
            "registration": 1000,
            "total": 78000
        }
    
    @staticmethod
    async def check_dues(user_id: str) -> Dict:
        return {"total_due": 25000, "paid": 15000, "pending": 10000, "due_date": "2024-04-15"}
    
    @staticmethod
    async def get_scholarships() -> List[Dict]:
        return [
            {"name": "Merit Scholarship", "amount": 20000, "criteria": "CGPA > 3.5", "deadline": "2024-03-31"},
            {"name": "Financial Aid", "amount": 15000, "criteria": "Income based", "deadline": "2024-04-15"},
        ]


class VisionTools:
    @staticmethod
    async def analyze_screen(image_data: str) -> Dict:
        return {
            "description": "Code editor with Python code visible",
            "detected": ["terminal", "code editor", "file explorer"],
            "language": "Python",
            "confidence": 0.92
        }
    
    @staticmethod
    async def extract_text(image_data: str) -> Dict:
        return {"text": "Extracted code from screenshot", "confidence": 0.95}
    
    @staticmethod
    async def analyze_diagram(image_data: str) -> Dict:
        return {"type": "flowchart", "nodes": 5, "edges": 4, "description": "System architecture diagram"}


# ============================================================================
# MCP SERVER
# ============================================================================

class MCPServer:
    def __init__(self):
        self.registry = ToolRegistry()
        self.cache = ToolCache()
        self.rate_limiter = RateLimiter()
        self.input_sanitizer = InputSanitizer()
        self._register_all_tools()
    
    def _register_all_tools(self):
        # Academic Tools
        self.registry.register(ToolDefinition(
            name="get_cgpa",
            description="Get student's current CGPA and academic standing",
            category=ToolCategory.ACADEMIC,
            input_schema={
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"]
            },
            permissions=[Permission.STUDENT, Permission.FACULTY, Permission.ADMIN],
            execute=AcademicTools.get_cgpa
        ))
        
        self.registry.register(ToolDefinition(
            name="get_courses",
            description="Get courses for a specific semester",
            category=ToolCategory.ACADEMIC,
            input_schema={
                "type": "object",
                "properties": {"semester": {"type": "integer", "minimum": 1, "maximum": 12}},
                "required": []
            },
            permissions=[Permission.STUDENT],
            execute=AcademicTools.get_courses
        ))
        
        self.registry.register(ToolDefinition(
            name="check_prerequisites",
            description="Check course prerequisites",
            category=ToolCategory.ACADEMIC,
            input_schema={
                "type": "object",
                "properties": {"course_code": {"type": "string"}},
                "required": ["course_code"]
            },
            permissions=[Permission.STUDENT],
            execute=AcademicTools.check_prerequisites
        ))
        
        # Library Tools
        self.registry.register(ToolDefinition(
            name="search_books",
            description="Search library books and journals",
            category=ToolCategory.LIBRARY,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "maxLength": 200},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50}
                },
                "required": ["query"]
            },
            permissions=[Permission.STUDENT, Permission.FACULTY, Permission.PUBLIC],
            cache_ttl=300,
            execute=LibraryTools.search_books
        ))
        
        self.registry.register(ToolDefinition(
            name="check_book_availability",
            description="Check if a specific book is available",
            category=ToolCategory.LIBRARY,
            input_schema={
                "type": "object",
                "properties": {"book_title": {"type": "string"}},
                "required": ["book_title"]
            },
            permissions=[Permission.STUDENT],
            execute=LibraryTools.check_availability
        ))
        
        self.registry.register(ToolDefinition(
            name="get_seat_availability",
            description="Get library seat availability",
            category=ToolCategory.LIBRARY,
            input_schema={"type": "object", "properties": {}},
            permissions=[Permission.STUDENT],
            realtime=True,
            execute=LibraryTools.get_seat_availability
        ))
        
        # Campus Tools
        self.registry.register(ToolDefinition(
            name="get_shuttle_schedule",
            description="Get shuttle/bus schedule",
            category=ToolCategory.CAMPUS,
            input_schema={"type": "object", "properties": {}},
            permissions=[Permission.STUDENT, Permission.FACULTY],
            realtime=True,
            execute=CampusTools.get_shuttle_schedule
        ))
        
        self.registry.register(ToolDefinition(
            name="get_shuttle_location",
            description="Track shuttle in real-time",
            category=ToolCategory.CAMPUS,
            input_schema={
                "type": "object",
                "properties": {"route": {"type": "string"}},
                "required": ["route"]
            },
            permissions=[Permission.STUDENT],
            realtime=True,
            execute=CampusTools.get_shuttle_location
        ))
        
        self.registry.register(ToolDefinition(
            name="get_notices",
            description="Get campus notices and announcements",
            category=ToolCategory.CAMPUS,
            input_schema={
                "type": "object",
                "properties": {"category": {"type": "string"}}
            },
            permissions=[Permission.STUDENT, Permission.FACULTY, Permission.PUBLIC],
            execute=CampusTools.get_notices
        ))
        
        # Career Tools
        self.registry.register(ToolDefinition(
            name="search_jobs",
            description="Search job opportunities",
            category=ToolCategory.CAREER,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "maximum": 20}
                },
                "required": ["query"]
            },
            permissions=[Permission.STUDENT],
            cache_ttl=600,
            execute=CareerTools.search_jobs
        ))
        
        self.registry.register(ToolDefinition(
            name="analyze_cv",
            description="Analyze and score CV/resume",
            category=ToolCategory.CAREER,
            input_schema={
                "type": "object",
                "properties": {"cv_text": {"type": "string", "maxLength": 10000}},
                "required": ["cv_text"]
            },
            permissions=[Permission.STUDENT],
            execute=CareerTools.analyze_cv
        ))
        
        self.registry.register(ToolDefinition(
            name="generate_career_roadmap",
            description="Generate career development roadmap",
            category=ToolCategory.CAREER,
            input_schema={
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "current_level": {"type": "string"}
                },
                "required": ["role"]
            },
            permissions=[Permission.STUDENT],
            execute=CareerTools.generate_roadmap
        ))
        
        # Finance Tools
        self.registry.register(ToolDefinition(
            name="calculate_tuition",
            description="Calculate tuition fees for a semester",
            category=ToolCategory.FINANCE,
            input_schema={
                "type": "object",
                "properties": {"semester": {"type": "integer"}},
                "required": []
            },
            permissions=[Permission.STUDENT],
            execute=FinanceTools.get_tuition_fees
        ))
        
        self.registry.register(ToolDefinition(
            name="check_financial_dues",
            description="Check pending financial dues",
            category=ToolCategory.FINANCE,
            input_schema={
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"]
            },
            permissions=[Permission.STUDENT],
            execute=FinanceTools.check_dues
        ))
        
        self.registry.register(ToolDefinition(
            name="get_scholarships",
            description="Get available scholarships",
            category=ToolCategory.FINANCE,
            input_schema={"type": "object", "properties": {}},
            permissions=[Permission.STUDENT],
            cache_ttl=3600,
            execute=FinanceTools.get_scholarships
        ))
        
        # Vision Tools
        self.registry.register(ToolDefinition(
            name="analyze_screen",
            description="Analyze screen/UI in real-time",
            category=ToolCategory.VISION,
            input_schema={
                "type": "object",
                "properties": {"image_data": {"type": "string"}},
                "required": ["image_data"]
            },
            permissions=[Permission.STUDENT],
            realtime=True,
            execute=VisionTools.analyze_screen
        ))
        
        self.registry.register(ToolDefinition(
            name="extract_text_from_image",
            description="OCR - Extract text from image/screenshot",
            category=ToolCategory.VISION,
            input_schema={
                "type": "object",
                "properties": {"image_data": {"type": "string"}},
                "required": ["image_data"]
            },
            permissions=[Permission.STUDENT],
            execute=VisionTools.extract_text
        ))
        
        logger.info(f"Registered {len(self.registry.tools)} tools")
    
    async def execute_tool(self, request: ToolRequest) -> ToolResponse:
        start_time = time.time()
        request_id = hashlib.sha256(f"{request.tool_name}{time.time()}".encode()).hexdigest()[:16]
        
        # 1. Check rate limit
        rate_key = f"{request.user_id or 'anonymous'}:{request.tool_name}"
        if not await self.rate_limiter.check_limit(rate_key, 100):
            return ToolResponse(
                success=False,
                tool=request.tool_name,
                error="Rate limit exceeded",
                source="rate_limiter"
            )
        
        # 2. Get tool definition
        tool = self.registry.get(request.tool_name)
        if not tool:
            return ToolResponse(
                success=False,
                tool=request.tool_name,
                error="Tool not found"
            )
        
        # 3. Check permissions
        user_permission = Permission(request.role) if request.role in [p.value for p in Permission] else Permission.STUDENT
        if user_permission not in tool.permissions and Permission.PUBLIC not in tool.permissions:
            return ToolResponse(
                success=False,
                tool=request.tool_name,
                error="Insufficient permissions"
            )
        
        # 4. Validate parameters
        validated_params = {}
        try:
            for key, schema in tool.input_schema.get("properties", {}).items():
                if key in request.parameters:
                    value = request.parameters[key]
                    
                    if schema.get("type") == "string":
                        value = self.input_sanitizer.sanitize_string(value, schema.get("maxLength", 1000))
                    elif schema.get("type") == "integer":
                        value = self.input_sanitizer.sanitize_integer(
                            value,
                            schema.get("minimum"),
                            schema.get("maximum")
                        )
                    
                    validated_params[key] = value
        except ValueError as e:
            return ToolResponse(
                success=False,
                tool=request.tool_name,
                error=f"Invalid parameter: {str(e)}"
            )
        
        # 5. Check cache
        if not tool.realtime:
            cache_key = f"{request.tool_name}:{json.dumps(validated_params, sort_keys=True)}"
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return ToolResponse(
                    success=True,
                    tool=request.tool_name,
                    data=cached_data,
                    cached=True,
                    latency_ms=(time.time() - start_time) * 1000,
                    source="cache"
                )
        
        # 6. Execute tool
        try:
            if tool.execute:
                data = await tool.execute(**validated_params)
                
                # Cache if not realtime
                if not tool.realtime:
                    cache_key = f"{request.tool_name}:{json.dumps(validated_params, sort_keys=True)}"
                    await self.cache.set(cache_key, data, tool.cache_ttl)
                
                return ToolResponse(
                    success=True,
                    tool=request.tool_name,
                    data=data,
                    latency_ms=(time.time() - start_time) * 1000,
                    source="database" if not tool.realtime else "realtime"
                )
            else:
                return ToolResponse(
                    success=False,
                    tool=request.tool_name,
                    error="Tool not implemented"
                )
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolResponse(
                success=False,
                tool=request.tool_name,
                error=str(e)
            )
    
    def get_available_tools(self) -> Dict:
        return self.registry.get_schema()


# ============================================================================
# FASTAPI SERVER
# ============================================================================

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="DI MCP Tool Server")
mcp_server = MCPServer()


class ToolRequestModel(BaseModel):
    tool_name: str
    parameters: Dict = {}
    role: str = "student"


@app.get("/")
async def root():
    return {
        "service": "Daffodil Intelligence MCP Server",
        "version": "1.0.0",
        "tools": len(mcp_server.registry.tools)
    }


@app.get("/tools")
async def list_tools(authorization: str = Header(None)):
    return mcp_server.get_available_tools()


@app.post("/tools/execute")
async def execute_tool(
    request: ToolRequestModel,
    authorization: str = Header(None)
):
    tool_request = ToolRequest(
        tool_name=request.tool_name,
        parameters=request.parameters,
        role=request.role
    )
    
    result = await mcp_server.execute_tool(tool_request)
    
    return {
        "success": result.success,
        "tool": result.tool,
        "data": result.data,
        "error": result.error,
        "latency_ms": round(result.latency_ms, 2),
        "source": result.source,
        "cached": result.cached
    }


@app.get("/tools/{tool_name}")
async def tool_info(tool_name: str):
    tool = mcp_server.registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return {
        "name": tool.name,
        "description": tool.description,
        "category": tool.category.value,
        "permissions": [p.value for p in tool.permissions],
        "realtime": tool.realtime,
        "input_schema": tool.input_schema
    }


@app.post("/tools/cache/invalidate")
async def invalidate_cache(pattern: str = None):
    await mcp_server.cache.invalidate(pattern)
    return {"status": "cache_cleared"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "tools_registered": len(mcp_server.registry.tools),
        "cache_size": len(mcp_server.cache.cache)
    }


if __name__ == "__main__":
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)