"""
University Domain Tools
=======================
Expose the ``university_data`` connector (SIS, library, transport, HR, exam) as
first-class agent tools so the main Antigravity agent can answer academic,
library, transport, career and exam questions natively via tool calls.

These replace the old per-agent keyword handlers: the agent now decides when to
call ``get_cgpa`` etc. instead of the supervisor string-matching keywords.
"""

from ..base import BaseTool, ToolParameter, ToolResult
from ...core.university_data import university_data


class GetCgpaTool(BaseTool):
    name = "get_cgpa"
    description = "Get a student's current CGPA by student ID."
    category = "academic"
    parameters = [
        ToolParameter(name="student_id", type="string", description="University student ID"),
    ]

    async def execute(self, student_id: str) -> ToolResult:
        try:
            cgpa = await university_data.get_cgpa(student_id)
            return self.ok({"student_id": student_id, "cgpa": cgpa})
        except Exception as e:
            return self.fail(str(e))


class GetCoursesTool(BaseTool):
    name = "get_courses"
    description = "List a student's enrolled courses (optionally for a semester)."
    category = "academic"
    parameters = [
        ToolParameter(name="student_id", type="string", description="University student ID"),
        ToolParameter(name="semester", type="string", description="Semester filter e.g. 'Spring 2026'", required=False),
    ]

    async def execute(self, student_id: str, semester: str = None) -> ToolResult:
        try:
            courses = await university_data.get_courses(student_id, semester)
            return self.ok({"student_id": student_id, "courses": courses})
        except Exception as e:
            return self.fail(str(e))


class GetAttendanceTool(BaseTool):
    name = "get_attendance"
    description = "Get a student's attendance overview (optionally per course)."
    category = "academic"
    parameters = [
        ToolParameter(name="student_id", type="string", description="University student ID"),
        ToolParameter(name="course_code", type="string", description="Course code filter e.g. 'CSE321'", required=False),
    ]

    async def execute(self, student_id: str, course_code: str = None) -> ToolResult:
        try:
            data = await university_data.get_attendance(student_id, course_code)
            return self.ok(data)
        except Exception as e:
            return self.fail(str(e))


class GetStudentInfoTool(BaseTool):
    name = "get_student_info"
    description = "Get basic profile information for a student by ID."
    category = "academic"
    parameters = [
        ToolParameter(name="student_id", type="string", description="University student ID"),
    ]

    async def execute(self, student_id: str) -> ToolResult:
        try:
            info = await university_data.get_student_info(student_id)
            return self.ok(info)
        except Exception as e:
            return self.fail(str(e))


class GetExamScheduleTool(BaseTool):
    name = "get_exam_schedule"
    description = "Get a student's upcoming exam schedule (optionally per semester)."
    category = "academic"
    parameters = [
        ToolParameter(name="student_id", type="string", description="University student ID"),
        ToolParameter(name="semester", type="string", description="Semester filter", required=False),
    ]

    async def execute(self, student_id: str, semester: str = None) -> ToolResult:
        try:
            exams = await university_data.get_exam_schedule(student_id, semester)
            return self.ok({"student_id": student_id, "exams": exams})
        except Exception as e:
            return self.fail(str(e))


class SearchBooksTool(BaseTool):
    name = "search_books"
    description = "Search the university library catalogue for books."
    category = "library"
    parameters = [
        ToolParameter(name="query", type="string", description="Title/keyword to search for"),
        ToolParameter(name="limit", type="integer", description="Max results (default 10)", required=False, default=10),
    ]

    async def execute(self, query: str, limit: int = 10) -> ToolResult:
        try:
            books = await university_data.search_books(query, limit)
            return self.ok({"query": query, "books": books})
        except Exception as e:
            return self.fail(str(e))


class GetBookAvailabilityTool(BaseTool):
    name = "get_book_availability"
    description = "Check availability and shelf locations for a library book by ID."
    category = "library"
    parameters = [
        ToolParameter(name="book_id", type="string", description="Library book ID"),
    ]

    async def execute(self, book_id: str) -> ToolResult:
        try:
            data = await university_data.get_book_availability(book_id)
            return self.ok(data)
        except Exception as e:
            return self.fail(str(e))


class GetShuttleScheduleTool(BaseTool):
    name = "get_shuttle_schedule"
    description = "Get the campus shuttle/transport schedule (optionally by route)."
    category = "transport"
    parameters = [
        ToolParameter(name="route", type="string", description="Route name filter e.g. 'Uttara'", required=False),
    ]

    async def execute(self, route: str = None) -> ToolResult:
        try:
            schedules = await university_data.get_shuttle_schedule(route)
            return self.ok({"route": route, "schedules": schedules})
        except Exception as e:
            return self.fail(str(e))


class GetJobsTool(BaseTool):
    name = "get_jobs"
    description = "List job openings from the university career portal."
    category = "career"
    parameters = [
        ToolParameter(name="query", type="string", description="Keyword/title filter", required=False),
        ToolParameter(name="limit", type="integer", description="Max results (default 20)", required=False, default=20),
    ]

    async def execute(self, query: str = None, limit: int = 20) -> ToolResult:
        try:
            jobs = await university_data.get_jobs(query, limit)
            return self.ok({"query": query, "jobs": jobs})
        except Exception as e:
            return self.fail(str(e))


class GetInternshipsTool(BaseTool):
    name = "get_internships"
    description = "List internship opportunities from the career portal."
    category = "career"
    parameters = [
        ToolParameter(name="query", type="string", description="Keyword/title filter", required=False),
    ]

    async def execute(self, query: str = None) -> ToolResult:
        try:
            internships = await university_data.get_internships(query)
            return self.ok({"query": query, "internships": internships})
        except Exception as e:
            return self.fail(str(e))
