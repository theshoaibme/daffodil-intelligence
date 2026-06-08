"""Computer control tools — screenshot, mouse, keyboard."""
import time
from ..base import BaseTool, ToolParameter, ToolResult


class TakeScreenshotTool(BaseTool):
    name = "take_screenshot"
    description = "Capture the current screen as a JPEG image (base64 encoded)"
    category = "computer"
    parameters = [
        ToolParameter(name="region", type="string", description="Optional region 'x,y,width,height' (e.g. '0,0,1920,1080')", required=False),
        ToolParameter(name="quality", type="integer", description="JPEG quality 1-95 (default 75)", required=False, default=75),
    ]

    async def execute(self, region: str = None, quality: int = 75) -> ToolResult:
        from ...computer_use.screen import ScreenCapture
        sc = ScreenCapture(quality=quality)

        if region:
            try:
                x, y, w, h = [int(v) for v in region.split(",")]
                b64 = sc.capture_as_base64(region=(x, y, w, h))
            except ValueError:
                return self.fail("Invalid region format. Use 'x,y,width,height'")
        else:
            b64 = sc.capture_as_base64()

        if b64:
            width, height = sc.get_screen_size()
            return self.ok({"image_b64": b64, "width": width, "height": height, "format": "jpeg"})
        return self.fail("Screen capture failed — no capture library available")


class MouseMoveTool(BaseTool):
    name = "mouse_move"
    description = "Move the agent cursor to screen coordinates"
    category = "computer"
    parameters = [
        ToolParameter(name="x", type="integer", description="Target X coordinate in pixels"),
        ToolParameter(name="y", type="integer", description="Target Y coordinate in pixels"),
        ToolParameter(name="duration", type="number", description="Animation duration in seconds (default 0.2)", required=False, default=0.2),
    ]

    async def execute(self, x: int, y: int, duration: float = 0.2) -> ToolResult:
        from ...computer_use.mouse import MouseController
        mc = MouseController()
        result = await mc.move(x, y, duration)
        if result.get("success"):
            return self.ok(result)
        return self.fail(result.get("error", "Move failed"))


class MouseClickTool(BaseTool):
    name = "mouse_click"
    description = "Move to coordinates and click"
    category = "computer"
    parameters = [
        ToolParameter(name="x", type="integer", description="X coordinate to click"),
        ToolParameter(name="y", type="integer", description="Y coordinate to click"),
        ToolParameter(name="button", type="string", description="Mouse button: 'left', 'right', 'middle' (default 'left')", required=False, default="left"),
    ]

    async def execute(self, x: int, y: int, button: str = "left") -> ToolResult:
        from ...computer_use.mouse import MouseController
        mc = MouseController()
        result = await mc.click(x, y, button)
        if result.get("success"):
            return self.ok(result)
        return self.fail(result.get("error", "Click failed"))


class MouseScrollTool(BaseTool):
    name = "mouse_scroll"
    description = "Scroll at screen position"
    category = "computer"
    parameters = [
        ToolParameter(name="x", type="integer", description="X coordinate to scroll at"),
        ToolParameter(name="y", type="integer", description="Y coordinate to scroll at"),
        ToolParameter(name="dy", type="integer", description="Scroll amount (positive=up, negative=down)", required=False, default=-3),
    ]

    async def execute(self, x: int, y: int, dy: int = -3) -> ToolResult:
        from ...computer_use.mouse import MouseController
        mc = MouseController()
        result = await mc.scroll(x, y, dy)
        if result.get("success"):
            return self.ok(result)
        return self.fail(result.get("error", "Scroll failed"))


class KeyboardTypeTool(BaseTool):
    name = "keyboard_type"
    description = "Type text using the keyboard"
    category = "computer"
    parameters = [
        ToolParameter(name="text", type="string", description="Text to type"),
        ToolParameter(name="interval", type="number", description="Delay between keystrokes in seconds (default 0.02)", required=False, default=0.02),
    ]

    async def execute(self, text: str, interval: float = 0.02) -> ToolResult:
        from ...computer_use.keyboard import KeyboardController
        kb = KeyboardController()
        result = await kb.type_text(text, interval)
        if result.get("success"):
            return self.ok(result)
        return self.fail(result.get("error", "Typing failed"))


class KeyboardHotkeyTool(BaseTool):
    name = "keyboard_hotkey"
    description = "Press a keyboard shortcut combination (e.g. Ctrl+C, Alt+F4)"
    category = "computer"
    parameters = [
        ToolParameter(name="keys", type="string", description="Comma-separated keys e.g. 'ctrl,c' or 'ctrl,shift,s'"),
    ]

    async def execute(self, keys: str) -> ToolResult:
        from ...computer_use.keyboard import KeyboardController
        kb = KeyboardController()
        key_list = [k.strip() for k in keys.split(",")]
        result = await kb.hotkey(*key_list)
        if result.get("success"):
            return self.ok(result)
        return self.fail(result.get("error", "Hotkey failed"))


class GetScreenSizeTool(BaseTool):
    name = "get_screen_size"
    description = "Get the dimensions of the primary monitor"
    category = "computer"
    parameters = []

    async def execute(self) -> ToolResult:
        from ...computer_use.screen import ScreenCapture
        sc = ScreenCapture()
        w, h = sc.get_screen_size()
        return self.ok({"width": w, "height": h})
