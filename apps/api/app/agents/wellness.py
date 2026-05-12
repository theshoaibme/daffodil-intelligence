from .base import BaseAgent
from typing import Optional, Dict


class WellnessAgent(BaseAgent):
    name = "Wellness Agent"
    description = "Mental health support, stress management, study tips (non-medical advice only)"
    tools = ["stress_tips", "study_advice", "motivation", "schedule_tips", "breathing_exercises"]

    SYSTEM_PROMPT = """You are the Wellness Agent for DI.
You provide:
- Stress management techniques
- Study tips and productivity
- Motivation and encouragement
- Time management advice
- Relaxation exercises

IMPORTANT: You are NOT a medical professional. Always recommend seeking professional help for serious issues."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["stress", "anxious", "overwhelmed"]):
            return await self.handle_stress()

        elif any(k in message_lower for k in ["study", "focus", "concentrate"]):
            return await self.handle_study()

        elif any(k in message_lower for k in ["motivation", "motivate", "encourage"]):
            return await self.handle_motivation()

        elif any(k in message_lower for k in ["breathing", "relax", "calm"]):
            return await self.handle_breathing()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_stress(self) -> str:
        tips = await stress_tips()
        tip_list = "\n".join([f"- {t}" for t in tips])
        return f"""🧘 **Stress Management**

{tip_list}

Remember: Take breaks, stay hydrated, and talk to someone if needed.
For serious concerns, please contact the counseling center."""

    async def handle_study(self) -> str:
        return """📝 **Study Tips**

1. Use Pomodoro Technique (25 min study, 5 min break)
2. Active recall - test yourself while studying
3. Spaced repetition for long-term memory
4. Teach what you learn to someone else
5. Keep your study space organized"""

    async def handle_motivation(self) -> str:
        return """🌟 **Motivation**

Remember:
- You've overcome challenges before
- Every step forward counts
- It's okay to take breaks
- Progress, not perfection
- You're capable of great things!

One day at a time. You've got this! 💪"""

    async def handle_breathing(self) -> str:
        exercises = await breathing_exercises()
        return f"""🌬️ **Breathing Exercises**

**Box Breathing:**
{exercises['box_breathing']}

**4-7-8 Breathing:**
{exercises['478_breathing']}

Practice these when feeling stressed."""


async def stress_tips() -> list[str]:
    return [
        "Take short breaks every 25 minutes (Pomodoro technique)",
        "Practice deep breathing: 4-7-8 rule",
        "Exercise for at least 30 minutes",
        "Talk to friends or counselors",
        "Maintain a regular sleep schedule"
    ]


async def breathing_exercises() -> dict:
    return {
        "box_breathing": "Inhale 4s, hold 4s, exhale 4s, hold 4s - repeat 4 times",
        "478_breathing": "Inhale 4s, hold 7s, exhale 8s - repeat 3 times"
    }