"""
Computer Use Agent
==================
Controls the host machine's mouse, keyboard, and screen.
Accepts natural language instructions and translates them
to precise screen interactions using vision + action.

Examples:
  "Click the Save button"
  "Type 'hello world' into the search box"
  "Scroll down on the current page"
  "Take a screenshot and describe what you see"
  "Open Firefox and go to google.com"
"""

import asyncio
import base64
import logging
from typing import Optional

from .base import BaseAgent
from ..computer_use.screen import ScreenCapture
from ..computer_use.mouse import MouseController
from ..computer_use.keyboard import KeyboardController

logger = logging.getLogger(__name__)


class ComputerUseAgent(BaseAgent):
    name = "Computer Use Agent"
    description = (
        "Controls the host machine — mouse, keyboard, and screen. "
        "Can see the screen in real-time and perform any GUI action."
    )
    tools = [
        "take_screenshot",
        "mouse_move",
        "mouse_click",
        "mouse_scroll",
        "mouse_drag",
        "keyboard_type",
        "keyboard_hotkey",
        "keyboard_press",
        "get_screen_size",
        "analyze_screen",
        "find_and_click",
        "open_application",
    ]

    SYSTEM_PROMPT = """You are the Computer Use Agent for Daffodil Intelligence.
You control the user's computer screen, mouse, and keyboard.

When given a task, you:
1. Take a screenshot to see the current screen state
2. Analyze the screen to understand the layout
3. Determine the precise (x, y) coordinates for any required clicks
4. Execute mouse and keyboard actions step by step
5. Take follow-up screenshots to confirm success

Rules:
- Always verify the screen state before acting
- Be precise with coordinates — use vision to locate elements
- Report every action you take
- If an action fails, try an alternative approach
- Never perform destructive actions without explicit confirmation

Available tools:
- take_screenshot: Capture the current screen
- mouse_click(x, y, button): Click at screen coordinates
- mouse_move(x, y): Move cursor to coordinates  
- mouse_scroll(x, y, dy): Scroll at position
- keyboard_type(text): Type text
- keyboard_hotkey(keys): Press key combination e.g. ["ctrl", "c"]
- keyboard_press(key): Press a single key

Always respond with what action you're taking and why.
"""

    def __init__(self):
        super().__init__()
        self._screen = ScreenCapture(fps=5, quality=80)
        self._mouse = MouseController()
        self._keyboard = KeyboardController()
        self._action_log: list = []

    async def process(self, message: str, context: Optional[dict] = None) -> str:
        """
        Process a natural language computer use instruction.
        Uses vision + LLM to determine and execute required actions.
        """
        # Take a screenshot to give the LLM context
        screenshot_b64 = self._screen.capture_as_base64()

        if screenshot_b64:
            screen_context = f"\n[Screenshot captured — {self._screen.get_screen_size()[0]}x{self._screen.get_screen_size()[1]} screen]"
        else:
            screen_context = "\n[Screenshot not available — operating without visual context]"

        # Build the prompt with screen context
        augmented_message = f"{message}{screen_context}"

        try:
            # Use vision-capable model if screenshot available
            if screenshot_b64:
                response = await self._process_with_vision(
                    message, screenshot_b64, context
                )
            else:
                response = await self.generate_response(
                    self.SYSTEM_PROMPT, augmented_message
                )

            # Log the action
            self._action_log.append({
                "instruction": message,
                "response": response[:200],
                "had_screenshot": screenshot_b64 is not None,
            })

            return response

        except Exception as e:
            logger.error(f"ComputerUseAgent error: {e}")
            return f"Computer Use Agent encountered an error: {str(e)}"

    async def take_screenshot(self) -> Optional[str]:
        """Capture screen, return base64 JPEG."""
        return self._screen.capture_as_base64()

    async def click(self, x: int, y: int, button: str = "left") -> dict:
        """Click at screen coordinates."""
        result = await self._mouse.click(x, y, button)
        self._action_log.append({"action": "click", "x": x, "y": y, "button": button, **result})
        return result

    async def type_text(self, text: str) -> dict:
        """Type text using the keyboard."""
        result = await self._keyboard.type_text(text)
        self._action_log.append({"action": "type", "text": text[:50], **result})
        return result

    async def hotkey(self, *keys: str) -> dict:
        """Send a keyboard shortcut."""
        result = await self._keyboard.hotkey(*keys)
        self._action_log.append({"action": "hotkey", "keys": list(keys), **result})
        return result

    async def scroll(self, x: int, y: int, dy: int = -3) -> dict:
        """Scroll at a screen position."""
        result = await self._mouse.scroll(x, y, dy)
        self._action_log.append({"action": "scroll", "x": x, "y": y, "dy": dy, **result})
        return result

    def get_action_log(self) -> list:
        """Return the list of all actions taken."""
        return self._action_log.copy()

    def clear_action_log(self):
        """Clear the action history."""
        self._action_log.clear()

    # ─── Private ─────────────────────────────────────────────────────────────

    async def _process_with_vision(
        self, message: str, screenshot_b64: str, context: Optional[dict]
    ) -> str:
        """Use Gemini Vision to analyze screen and plan actions."""
        from ..core.config import get_settings
        settings = get_settings()

        if not settings.GEMINI_API_KEY:
            # Fall back to text-only
            return await self.generate_response(self.SYSTEM_PROMPT, message)

        import httpx

        vision_prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"User instruction: {message}\n\n"
            "The screenshot above shows the current screen state. "
            "Analyze it and describe what actions you would take to fulfill the instruction. "
            "Provide specific pixel coordinates for any clicks."
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}",
                    json={
                        "contents": [{
                            "parts": [
                                {
                                    "inline_data": {
                                        "mime_type": "image/jpeg",
                                        "data": screenshot_b64,
                                    }
                                },
                                {"text": vision_prompt}
                            ]
                        }],
                        "generationConfig": {
                            "temperature": 0.2,
                            "maxOutputTokens": 1024,
                        }
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return (
                        result.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "Could not analyze screen")
                    )
                else:
                    logger.warning(f"Gemini vision API error: {response.status_code}")
                    return await self.generate_response(self.SYSTEM_PROMPT, message)

        except Exception as e:
            logger.error(f"Vision processing failed: {e}")
            return await self.generate_response(self.SYSTEM_PROMPT, message)
