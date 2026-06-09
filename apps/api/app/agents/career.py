from .base import BaseAgent
from typing import Optional, Dict
from ..core.university_data import university_data


class CareerAgent(BaseAgent):
    name = "Career Agent"
    description = "Handles job opportunities, CV/resume help, career roadmap, interview preparation"
    tools = ["search_jobs", "review_cv", "generate_roadmap", "mock_interview", "get_internships"]

    SYSTEM_PROMPT = """You are the Career Agent for Daffodil Intelligence.
You help students with:
- Finding job and internship opportunities
- CV/resume review and suggestions
- Career path planning
- Interview preparation
- Professional development"""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["job", "vacancy", "opening"]):
            return await self.handle_jobs(message)

        elif any(k in message_lower for k in ["cv", "resume"]):
            return await self.handle_cv()

        elif any(k in message_lower for k in ["roadmap", "career path"]):
            return await self.handle_roadmap()

        elif any(k in message_lower for k in ["interview"]):
            return await self.handle_interview()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_jobs(self, message: str) -> str:
        jobs = await search_jobs("software")
        job_list = "\n".join([f"- **{j['title']}** at {j['company']} | {j['location']} | Deadline: {j['deadline']}" for j in jobs])
        return f"💼 **Job Opportunities**\n\n{job_list}\n\nApply through career portal."

    async def handle_cv(self) -> str:
        return "📄 **CV Review**\n\nUpload your CV and I'll analyze it for structure, content, and ATS optimization."

    async def handle_roadmap(self) -> str:
        roadmap = await generate_roadmap("Software Engineer", "student")
        steps = "\n".join([f"{r['step']}. {r['action']} ({r['timeline']})" for r in roadmap])
        return f"🗺️ **Career Roadmap**\n\n{steps}"

    async def handle_interview(self) -> str:
        return "🎯 **Interview Prep**\n\nI can help with:\n1. Common questions\n2. Technical problems\n3. Behavioral questions\n\nType 'start mock interview' to begin."


async def search_jobs(query: str = None, limit: int = 20) -> list[dict]:
    return await university_data.get_jobs(query, limit)


async def review_cv(cv_text: str) -> dict:
    return {"score": 85, "strengths": ["Clear structure"], "improvements": ["Add metrics"]}


async def generate_roadmap(role: str, level: str) -> list[dict]:
    return [
        {"step": 1, "action": "Master fundamentals", "timeline": "3 months"},
        {"step": 2, "action": "Build projects", "timeline": "6 months"},
        {"step": 3, "action": "Apply for internships", "timeline": "9 months"},
    ]