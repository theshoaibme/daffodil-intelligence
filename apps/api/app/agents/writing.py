"""Writing & document productivity agent."""

from __future__ import annotations

from typing import Dict, Optional

from .base import BaseAgent
from .tool_runner import format_tool_results, run_tool


class WritingAgent(BaseAgent):
    name = "Writing Agent"
    description = "Drafts, edits, and summarizes documents, notes, and PDFs"
    tools = [
        "read_file",
        "write_file",
        "edit_file",
        "read_pdf",
        "search_directory",
        "find_file",
        "list_directory",
    ]

    SYSTEM_PROMPT = """You are the Writing Agent for Daffodil Intelligence.
You help with documents, notes, summaries, and file edits using read/write tools and PDFs."""

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        lower = message.lower()
        ctx = context or {}
        results = []

        if any(k in lower for k in ("pdf", ".pdf")):
            results.append(await run_tool("read_pdf", ctx, path=message))
        elif any(k in lower for k in ("read", "open", "show file")):
            results.append(await run_tool("read_file", ctx, path=message))
        elif any(k in lower for k in ("write", "save", "create file")):
            results.append(await run_tool("write_file", ctx, path="document.txt", content=message))
        elif any(k in lower for k in ("edit", "update", "replace")):
            results.append(await run_tool("edit_file", ctx, path=message))
        elif any(k in lower for k in ("find", "search file", "locate")):
            results.append(await run_tool("find_file", ctx, query=message))

        if results:
            return format_tool_results(results)
        return await self.generate_response(self.SYSTEM_PROMPT, message)
