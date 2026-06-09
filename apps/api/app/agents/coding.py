from .base import BaseAgent
from typing import Optional, Dict


class CodingAgent(BaseAgent):
    name = "Coding Agent"
    description = "Helps with code debugging, generation, explanation, and programming assistance"
    tools = ["debug_code", "generate_code", "explain_code", "review_code", "execute_code"]

    SYSTEM_PROMPT = """You are the Coding Agent for Daffodil Intelligence.
You help with:
- Debugging code errors
- Generating code snippets
- Explaining programming concepts
- Code review and best practices
- Multiple programming languages"""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["debug", "error", "bug", "fix"]):
            return await self.handle_debug(message)

        elif any(k in message_lower for k in ["generate", "write", "create", "code"]):
            return await self.handle_generate(message)

        elif any(k in message_lower for k in ["explain", "understand", "how"]):
            return await self.handle_explain(message)

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_debug(self, message: str) -> str:
        return f"""🐛 **Debug Help**

Received: {message}

Please share:
1. The code that's causing the error
2. The exact error message
3. What you expected to happen

I'll help you identify and fix the issue."""

    async def handle_generate(self, message: str) -> str:
        return f"""💻 **Code Generation**

To generate code, please specify:
1. Programming language
2. What the code should do
3. Any specific requirements

Example: "Write a Python function to reverse a string\""""

    async def handle_explain(self, message: str) -> str:
        return f"""📖 **Code Explanation**

To explain code, please share:
1. The code snippet
2. What specifically you want to understand

I'll provide a detailed explanation with time complexity."""


async def debug_code(code: str, error: str) -> dict:
    return {"issue": "Possible null pointer at line 5", "fix": "Add null check before accessing the object"}


async def explain_code(code: str) -> dict:
    return {"summary": "This is a binary search implementation", "time_complexity": "O(log n)", "space_complexity": "O(1)"}