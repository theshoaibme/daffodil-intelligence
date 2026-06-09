from .base import BaseAgent
from typing import Optional, Dict
import logging
from ..core.university_data import university_data

logger = logging.getLogger(__name__)

GRADE_POINTS = {'A+': 4.0, 'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D': 1.0, 'F': 0.0}


class AcademicAgent(BaseAgent):
    name = "Academic Agent"
    description = "Handles CGPA, results, courses, syllabus, and academic queries"
    tools = ["get_cgpa", "get_courses", "get_results", "get_syllabus", "calculate_gpa"]

    SYSTEM_PROMPT = """You are the Academic Agent for Daffodil Intelligence.
You help students with:
- CGPA calculation and analysis
- Course registration and details
- Academic results and grades
- Syllabus and curriculum
- Semester planning

Be precise with numbers. Never guess - use tools when available.
If you need to retrieve documents, use RAG."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["cgpa", "my gpa", "current cgpa"]):
            return await self.handle_cgpa(context)

        elif any(k in message_lower for k in ["course", "subject", "class"]):
            return await self.handle_courses(context)

        elif any(k in message_lower for k in ["result", "grade", "marks"]):
            return await self.handle_results(context)

        elif any(k in message_lower for k in ["syllabus", "curriculum"]):
            return await self.handle_syllabus(context)

        elif any(k in message_lower for k in ["calculate", "compute"]):
            return self.handle_calculation(message)

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_cgpa(self, context: Optional[Dict]) -> str:
        user_id = context.get("user_id", 1) if context else 1
        cgpa = await get_cgpa(user_id)

        if cgpa >= 3.5:
            status = "Excellent"
        elif cgpa >= 3.0:
            status = "Good"
        elif cgpa >= 2.5:
            status = "Average"
        else:
            status = "Needs Improvement"

        return f"""📊 **Your Current CGPA: {cgpa}**

Status: **{status}**
- Maintain above 3.5 for Dean's List
- Keep up the good work!

Need more details about your grades or courses?"""

    async def handle_courses(self, context: Optional[Dict]) -> str:
        user_id = context.get("user_id", 1) if context else 1
        semester = context.get("semester", 1) if context else 1
        courses = await get_courses(user_id, semester)

        course_list = "\n".join([
            f"- **{c['code']}**: {c['name']} ({c['credits']} credits) - {c.get('grade', 'N/A')}"
            for c in courses
        ])

        return f"""📚 **Your Courses (Semester {semester})**

{course_list}

Total Credits: {sum(c['credits'] for c in courses)}"""

    async def handle_results(self, context: Optional[Dict]) -> str:
        user_id = context.get("user_id", 1) if context else 1
        results = await get_results(user_id)

        return f"""📋 **Academic Results**

Semester: **{results['semester']}**
GPA: **{results['gpa']}**

Courses:
{chr(10).join([f"- {c['code']}: {c['name']} - {c['grade']} ({c['grade_point']})" for c in results['courses']])}"""

    async def handle_syllabus(self, context: Optional[Dict]) -> str:
        return """📖 **Syllabus Information**

I can help you find syllabus information. Please specify:
- Which course?
- Which semester?

I can also retrieve documents from the RAG system if available."""

    def handle_calculation(self, message: str) -> str:
        import re
        grades = re.findall(r'([A-F][+-]?)\s*:?\s*(\d+)', message.upper())

        if not grades:
            return "Please provide grades with credits like: A:3, B+:3"

        total_points = 0
        total_credits = 0

        for grade, credits in grades:
            gp = GRADE_POINTS.get(grade, 0)
            cr = int(credits)
            total_points += gp * cr
            total_credits += cr

        gpa = total_points / total_credits if total_credits > 0 else 0
        return f"📊 Calculated GPA: **{gpa:.2f}** (based on {total_credits} credits)"


async def get_cgpa(user_id: int) -> float:
    student_id = f"STU{user_id:05d}"
    return await university_data.get_cgpa(student_id)


async def get_courses(user_id: int, semester: int = None) -> list[dict]:
    student_id = f"STU{user_id:05d}"
    courses = await university_data.get_courses(student_id, str(semester) if semester else None)
    return [{"code": c["code"], "name": c["name"], "credits": c["credit"], "grade": c.get("grade", "N/A")} for c in courses]


async def get_results(user_id: int, semester: int = None) -> dict:
    student_id = f"STU{user_id:05d}"
    courses = await university_data.get_courses(student_id, str(semester) if semester else None)
    gpa = sum(GRADE_POINTS.get(c.get("grade", "F"), 0) * c.get("credit", 3) for c in courses) / sum(c.get("credit", 3) for c in courses) if courses else 0
    return {
        "semester": "Spring 2026",
        "gpa": round(gpa, 2),
        "courses": [
            {"code": c["code"], "name": c["name"], "grade": c.get("grade", "N/A"), "grade_point": GRADE_POINTS.get(c.get("grade", "F"), 0)}
            for c in courses
        ]
    }


def calculate_gpa(grades: list[tuple]) -> float:
    total_points = 0
    total_credits = 0
    for grade, credits in grades:
        gp = GRADE_POINTS.get(grade, 0)
        total_points += gp * credits
        total_credits += credits
    return round(total_points / total_credits, 2) if total_credits > 0 else 0