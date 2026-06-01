from .base import BaseAgent
from typing import Optional, Dict


class VoiceAgent(BaseAgent):
    name = "Voice Agent"
    description = "Speech-to-text, text-to-speech, and live voice conversation"
    tools = ["speech_to_text", "text_to_speech", "start_voice_call", "voice_commands"]

    SYSTEM_PROMPT = """You are the Voice Agent for Daffodil Intelligence.
You handle:
- Converting speech to text
- Converting text to speech
- Voice-based commands
- Live voice conversations
- Audio transcription"""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        message_lower = message.lower()

        if any(k in message_lower for k in ["speech", "speak", "talk"]):
            return await self.handle_speech_to_text()

        elif any(k in message_lower for k in ["text to speech", "tts", "read aloud"]):
            return await self.handle_text_to_speech()

        elif any(k in message_lower for k in ["voice call", "live", "conversation"]):
            return await self.handle_voice_call()

        return await self.generate_response(self.SYSTEM_PROMPT, message)

    async def handle_speech_to_text(self) -> str:
        return """🎙️ **Speech to Text**

To convert speech to text:
1. Click the microphone button
2. Speak your message
3. I'll transcribe it to text
4. You can then send as message

Works best in quiet environments."""

    async def handle_text_to_speech(self) -> str:
        return """🔊 **Text to Speech**

To hear text as speech:
1. Type your message
2. Click the speaker icon
3. I'll read it aloud
4. Choose voice preference in settings

Available voices: Aoede, Puck, Charon"""

    async def handle_voice_call(self) -> str:
        return """📞 **Voice Call**

To start a live voice conversation:
1. Go to /live page
2. Click "Start Voice Chat"
3. Speak naturally
4. Get real-time responses

Powered by Gemini Live API!"""


async def speech_to_text(audio_data: str) -> str:
    return "Converted text from speech"


async def text_to_speech(text: str, voice: str = "Aoede") -> str:
    return f"audio_url_for_{voice}"