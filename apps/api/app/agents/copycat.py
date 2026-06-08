"""
CopyCat Agent
=============
Records everything the user does and replays it on command.

When activated:
  - Records all mouse movements, clicks, scrolls
  - Records all keyboard presses and typed text
  - Can replay the entire session on demand
  - Shows its own distinct cursor overlay during replay
  - Optionally saves recordings as named macros

The "copycat" feature: whatever you do, it can copy.
"""

import asyncio
import logging
from typing import Optional

from .base import BaseAgent
from ..computer_use.recorder import ActionRecorder, get_recorder
from ..computer_use.replayer import ActionReplayer

logger = logging.getLogger(__name__)


class CopyCatAgent(BaseAgent):
    name = "CopyCat Agent"
    description = (
        "Records your mouse/keyboard actions and replays them on command. "
        "Like a macro recorder, but powered by AI."
    )
    tools = [
        "start_recording",
        "stop_recording",
        "replay_last",
        "replay_named",
        "save_recording",
        "list_recordings",
        "delete_recording",
        "replay_status",
    ]

    SYSTEM_PROMPT = """You are the CopyCat Agent for Daffodil Intelligence.
Your specialty is recording and replaying user actions on their computer.

When the user says things like:
- "start recording" / "শুরু কর" → Call start_recording
- "stop recording" / "বন্ধ কর" → Call stop_recording  
- "replay" / "আবার কর" / "repeat that" → Call replay_last
- "replay [name]" → Call replay_named with that name
- "save as [name]" → Call save_recording with that name
- "list recordings" / "কী কী আছে" → Call list_recordings

Explain what you're doing in a friendly way.
Always confirm before replaying destructive actions.
Respond in the same language as the user (English or Bengali).
"""

    def __init__(self):
        super().__init__()
        self._recorder = get_recorder()
        self._replayer = ActionReplayer()
        self._last_recording = None

    async def process(self, message: str, context: Optional[dict] = None) -> str:
        """Parse instruction and execute recording/replay action."""
        msg_lower = message.lower().strip()

        # Fast keyword matching for common commands
        if any(k in msg_lower for k in ["start rec", "শুরু কর", "রেকর্ড শুরু", "begin record", "record start"]):
            return await self._start_recording(message, context)

        if any(k in msg_lower for k in ["stop rec", "বন্ধ কর", "রেকর্ড বন্ধ", "end record", "record stop"]):
            return await self._stop_recording(context)

        if any(k in msg_lower for k in ["replay", "repeat", "আবার কর", "পুনরায়", "do again"]):
            # Check if a specific name is mentioned
            name = self._extract_recording_name(message)
            if name:
                return await self._replay_named(name, context)
            return await self._replay_last(context)

        if any(k in msg_lower for k in ["save as", "নাম দাও", "save recording"]):
            name = self._extract_recording_name(message) or "macro"
            return await self._save_recording(name, context)

        if any(k in msg_lower for k in ["list", "তালিকা", "কী আছে", "show recordings", "recordings"]):
            return await self._list_recordings(context)

        if any(k in msg_lower for k in ["delete", "মুছে", "remove recording"]):
            name = self._extract_recording_name(message)
            if name:
                return await self._delete_recording(name, context)

        # Fall back to LLM for nuanced instructions
        return await self.generate_response(self.SYSTEM_PROMPT, message)

    # ─── Command handlers ─────────────────────────────────────────────────────

    async def _start_recording(self, message: str, context: Optional[dict]) -> str:
        if self._recorder.is_recording:
            return (
                "⚠️ I'm already recording! Say **stop recording** first to end the current session."
                "\n\nইতিমধ্যে রেকর্ডিং চলছে। আগে বন্ধ করুন।"
            )

        name = self._extract_recording_name(message) or None
        success = self._recorder.start(name)

        if success:
            return (
                f"🔴 **Recording started!** {'(Named: ' + name + ')' if name else ''}\n\n"
                "I'm now watching everything you do — every mouse click, scroll, and keystroke. "
                "Say **stop recording** when you're done.\n\n"
                "রেকর্ডিং শুরু হয়েছে। আপনার সব কার্যকলাপ রেকর্ড হচ্ছে। শেষ করতে বলুন **stop recording**।"
            )
        else:
            return (
                "❌ Could not start recording. The `pynput` library may not be installed.\n"
                "Run: `pip install pynput`\n\n"
                "রেকর্ডিং শুরু করা যায়নি। pynput ইনস্টল করুন।"
            )

    async def _stop_recording(self, context: Optional[dict]) -> str:
        if not self._recorder.is_recording:
            return (
                "⚠️ No active recording to stop. Say **start recording** first.\n\n"
                "কোনো সক্রিয় রেকর্ডিং নেই।"
            )

        recording = self._recorder.stop()
        if recording:
            self._last_recording = recording
            duration = f"{recording.duration:.1f}s"
            actions = recording.action_count
            return (
                f"⏹️ **Recording stopped!**\n\n"
                f"- **Duration:** {duration}\n"
                f"- **Actions captured:** {actions}\n"
                f"- **Name:** {recording.name}\n\n"
                f"Say **replay** to repeat it, or **save as [name]** to keep it permanently.\n\n"
                f"রেকর্ডিং বন্ধ। {actions}টি কার্যকলাপ রেকর্ড হয়েছে। **replay** বলুন পুনরায় করতে।"
            )

        return "Recording stopped but no data was captured."

    async def _replay_last(self, context: Optional[dict]) -> str:
        if self._last_recording is None:
            recordings = self._recorder.list_recordings()
            if recordings:
                # Auto-load the most recent
                name = recordings[0]["name"]
                recording = self._recorder.load(name)
                if recording:
                    self._last_recording = recording
                else:
                    return "No recent recording to replay. Start a recording first."
            else:
                return (
                    "No recording found. Say **start recording** to capture your actions first.\n\n"
                    "কোনো রেকর্ডিং নেই। আগে **start recording** বলুন।"
                )

        return await self._do_replay(self._last_recording)

    async def _replay_named(self, name: str, context: Optional[dict]) -> str:
        recording = self._recorder.load(name)
        if not recording:
            recordings = self._recorder.list_recordings()
            available = ", ".join(r["name"] for r in recordings[:5])
            return (
                f"❌ Recording **'{name}'** not found.\n"
                f"Available recordings: {available or 'none'}\n\n"
                f"'{name}' নামের রেকর্ডিং পাওয়া যায়নি।"
            )

        return await self._do_replay(recording)

    async def _do_replay(self, recording) -> str:
        if self._replayer.is_running:
            return "⚠️ A replay is already running! Wait for it to finish."

        actions = recording.action_count
        duration = f"{recording.duration:.1f}s"

        # Launch replay in background so we don't block the API
        asyncio.create_task(self._replayer.replay(recording, speed=1.0))

        return (
            f"▶️ **Replaying: {recording.name}**\n\n"
            f"- **Actions:** {actions}\n"
            f"- **Original duration:** {duration}\n"
            f"- Playing at 1x speed...\n\n"
            f"Watch my cursor — I'll repeat exactly what was recorded! 🖱️\n\n"
            f"পুনরায় করা হচ্ছে। আমার কার্সর দেখুন — ঠিক আগের মতো করা হবে।"
        )

    async def _save_recording(self, name: str, context: Optional[dict]) -> str:
        if not self._last_recording:
            return "No recording to save. Record something first."

        self._last_recording.name = name
        path = self._recorder.save(self._last_recording)
        return (
            f"💾 **Saved as '{name}'**\n\n"
            f"Stored at: `{path}`\n"
            f"You can replay it anytime with: **replay {name}**\n\n"
            f"'{name}' নামে সংরক্ষণ করা হয়েছে।"
        )

    async def _list_recordings(self, context: Optional[dict]) -> str:
        recordings = self._recorder.list_recordings()
        if not recordings:
            return (
                "📂 No saved recordings yet.\n\n"
                "Start with: **start recording**\n\n"
                "এখনো কোনো রেকর্ডিং নেই।"
            )

        lines = ["📋 **Saved Recordings:**\n"]
        for i, r in enumerate(recordings[:10], 1):
            import datetime
            dt = datetime.datetime.fromtimestamp(r["created_at"]).strftime("%Y-%m-%d %H:%M")
            lines.append(
                f"{i}. **{r['name']}** — {r['action_count']} actions, {r['duration']:.1f}s ({dt})"
            )

        lines.append(f"\n💡 Say **replay [name]** to run any recording.")
        return "\n".join(lines)

    async def _delete_recording(self, name: str, context: Optional[dict]) -> str:
        success = self._recorder.delete(name)
        if success:
            return f"🗑️ Deleted recording: **{name}**\n\n'{name}' মুছে ফেলা হয়েছে।"
        return f"❌ Recording '{name}' not found."

    def _extract_recording_name(self, message: str) -> Optional[str]:
        """Try to extract a recording name from the message."""
        import re

        # "save as [name]", "named [name]", "called [name]", "replay [name]"
        patterns = [
            r'save as ["\']?([a-zA-Z0-9_\- ]+)["\']?',
            r'named? ["\']?([a-zA-Z0-9_\- ]+)["\']?',
            r'called ["\']?([a-zA-Z0-9_\- ]+)["\']?',
            r'replay ["\']?([a-zA-Z0-9_\- ]+)["\']?',
            r'delete ["\']?([a-zA-Z0-9_\- ]+)["\']?',
        ]

        for pattern in patterns:
            m = re.search(pattern, message, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                # Exclude trigger words
                if name.lower() not in ("recording", "macro", "last", "that"):
                    return name.replace(" ", "_").lower()

        return None
