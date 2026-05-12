from .base import BaseAgent
from typing import Optional, Dict, List
from ..core.university_data import university_data
import logging

logger = logging.getLogger(__name__)


class ExamAgent(BaseAgent):
    name = "Exam Agent"
    description = "Handles exam schedules, results, attendance, and academic calendar"
    tools = ["get_exam_schedule", "get_attendance", "get_academic_calendar", "view_marks", "calculate_gpa"]

    SYSTEM_PROMPT = """You are the Exam Agent for DI (Daffodil Intelligence).
You help students with:
- Exam schedules and seating arrangements
- Attendance records
- Academic calendar
- marks and grade analysis
- GPA calculation
- Exam rules and guidelines

Be precise with dates and times. Use tools for accurate information."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["exam", "test", "seating", "seat plan"]):
            return await self.handle_exam_schedule(context)

        elif any(k in message_lower for k in ["attendance", "present", "absent"]):
            return await self.handle_attendance(context)

        elif any(k in message_lower for k in ["calendar", "date", "schedule"]):
            return await self.handle_calendar()

        elif any(k in message_lower for k in ["marks", "grade", "result"]):
            return await self.handle_marks(context)

        elif any(k in message_lower for k in ["gpa", "cgpa", "calculate"]):
            return await self.handle_gpa(context)

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_exam_schedule(self, context: Optional[Dict] = None) -> str:
        student_id = context.get("user_id", 1) if context else 1
        exams = await university_data.get_exam_schedule(f"STU{student_id:05d}")

        if not exams:
            return "📅 **Exam Schedule**\n\nNo upcoming exams found."

        exam_list = "\n".join([
            f"- **{e['course']}**: {e['title']}\n  📅 {e['date']} at {e['time']}\n  📍 Room: {e['room']}"
            for e in exams
        ])

        return f"""📅 **Upcoming Exam Schedule**

{exam_list}

💡 Tip: Arrive 15 minutes early and bring your student ID!"""

    async def handle_attendance(self, context: Optional[Dict] = None) -> str:
        student_id = context.get("user_id", 1) if context else 1
        attendance = await university_data.get_attendance(f"STU{student_id:05d}")

        overall = attendance.get("overall", 0)
        courses = attendance.get("courses", {})

        course_list = "\n".join([
            f"- **{code}**: {percent}%"
            for code, percent in courses.items()
        ])

        status = "🟢 Excellent" if overall >= 90 else "🟡 Good" if overall >= 75 else "🔴 Needs Improvement"

        return f"""📊 **Attendance Report**

Overall: **{overall}%** - {status}

{course_list}

💡 Minimum 75% attendance is required to appear in exams."""

    async def handle_calendar(self) -> str:
        return """📆 **Academic Calendar 2026**

**Spring Semester:**
- Classes Start: January 15
- Midterm Exams: March 10-15
- Final Exams: May 15-25
- Semester Break: May 26 - August 15

**Fall Semester:**
- Classes Start: September 1
- Midterm Exams: October 15-20
- Final Exams: December 1-10

📱 Check the university portal for detailed schedule."""

    async def handle_marks(self, context: Optional[Dict] = None) -> str:
        student_id = context.get("user_id", 1) if context else 1
        courses = await university_data.get_courses(f"STU{student_id:05d}")

        marks_list = "\n".join([
            f"- **{c['code']}**: {c.get('grade', 'N/A')}"
            for c in courses
        ])

        return f"""📝 **Your Grades**

{marks_list}

💡 Contact your department office for detailed marks breakdown."""

    async def handle_gpa(self, context: Optional[Dict] = None) -> str:
        student_id = context.get("user_id", 1) if context else 1
        cgpa = await university_data.get_cgpa(f"STU{student_id:05d}")

        return f"""📊 **GPA Analysis**

Current CGPA: **{cgpa}**

**Grade Distribution:**
- A (90-100%): 🟢 Excellent
- B (80-89%): 🔵 Good  
- C (70-79%): 🟡 Average
- D (60-69%): 🟠 Below Average
- F (<60%): 🔴 Needs Improvement

Keep up the good work! 🎓"""


async def get_exam_schedule(student_id: str, semester: str = None) -> List[Dict]:
    return await university_data.get_exam_schedule(student_id)


async def get_attendance(student_id: str, course_code: str = None) -> Dict:
    return await university_data.get_attendance(student_id)


async def get_academic_calendar() -> List[Dict]:
    return [
        {"event": "Spring Classes Start", "date": "2026-01-15"},
        {"event": "Midterm Exams", "date": "2026-03-10"},
        {"event": "Final Exams", "date": "2026-05-15"},
        {"event": "Semester Break", "date": "2026-05-26"},
    ]


async def calculate_gpa(grades: List[Dict]) -> float:
    if not grades:
        return 0.0
    
    GRADE_POINTS = {'A+': 4.0, 'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D': 1.0, 'F': 0.0}
    
    total_points = 0
    total_credits = 0
    
    for g in grades:
        gp = GRADE_POINTS.get(g.get('grade', 'F'), 0)
        credit = g.get('credit', 3)
        total_points += gp * credit
        total_credits += credit
    
    return round(total_points / total_credits, 2) if total_credits > 0 else 0.0