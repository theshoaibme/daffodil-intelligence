"""CopyCat tools — record and replay desktop macros via the agent."""

from ..base import BaseTool, ToolParameter, ToolResult


class StartRecordingTool(BaseTool):
    name = "start_recording"
    description = "Start recording the user's mouse/keyboard actions into a named macro."
    category = "computer"
    parameters = [
        ToolParameter(name="name", type="string", description="Name for the recording", required=False),
    ]

    async def execute(self, name: str = None) -> ToolResult:
        from ...computer_use.recorder import get_recorder
        rec = get_recorder()
        if rec.is_recording:
            return self.fail("Already recording. Stop the current recording first.")
        ok = rec.start(name)
        if not ok:
            return self.fail("Could not start recording (pynput unavailable?).")
        return self.ok({"recording": True, "name": name})


class StopRecordingTool(BaseTool):
    name = "stop_recording"
    description = "Stop the current recording and save it to disk."
    category = "computer"
    parameters = []

    async def execute(self) -> ToolResult:
        from ...computer_use.recorder import get_recorder
        rec = get_recorder()
        recording = rec.stop()
        if recording is None:
            return self.fail("Not currently recording.")
        rec.save(recording)
        payload = {
            "name": recording.name,
            "action_count": recording.action_count,
            "duration": round(recording.duration, 2),
        }
        try:
            from ...skills.copycat import create_skill_from_recording
            skill = create_skill_from_recording(
                recording.name,
                action_count=recording.action_count,
                duration=recording.duration,
            )
            if skill:
                payload["skill"] = skill
        except Exception:
            pass
        return self.ok(payload)


class ListRecordingsTool(BaseTool):
    name = "list_recordings"
    description = "List all saved desktop macros/recordings."
    category = "computer"
    parameters = []

    async def execute(self) -> ToolResult:
        from ...computer_use.recorder import get_recorder
        return self.ok({"recordings": get_recorder().list_recordings()})


class ReplayRecordingTool(BaseTool):
    name = "replay_recording"
    description = "Replay a saved macro by name, optionally at a speed multiplier."
    category = "computer"
    parameters = [
        ToolParameter(name="name", type="string", description="Recording name to replay"),
        ToolParameter(name="speed", type="number", description="Playback speed (1.0 = normal)", required=False, default=1.0),
    ]

    async def execute(self, name: str, speed: float = 1.0) -> ToolResult:
        from ...computer_use.recorder import get_recorder
        from ...computer_use.replayer import ActionReplayer
        rec = get_recorder()
        recording = rec.load(name)
        if recording is None:
            return self.fail(f"Recording not found: {name}")
        replayer = ActionReplayer()
        result = await replayer.replay(recording, speed=speed)
        return self.ok(result)
