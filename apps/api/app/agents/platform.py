"""Platform-style agents (Cursor, Copilot, Antigravity, NotebookLM, Cloud Code, Automation)."""

from __future__ import annotations

from typing import Dict, Optional

from .base import BaseAgent
from .tool_runner import format_tool_results, run_tool


class AutomationAgent(BaseAgent):
    name = "Automation Agent"
    description = "Workflow automation — delegate to specialists, parallel agents, and runbooks"
    tools = [
        "invoke_agent",
        "parallel_invoke_agents",
        "list_agents",
    ]

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        return await self.generate_response(
            "You are the Automation Agent — delegate to specialists and coordinate multi-agent workflows.",
            message,
        )


class CursorAgent(BaseAgent):
    name = "Cursor Agent"
    description = "Agentic IDE — codebase edits, terminal, and multi-step coding tasks"
    tools = [
        "read_file",
        "write_file",
        "edit_file",
        "find_file",
        "search_directory",
        "run_shell_command",
        "run_python",
        "invoke_agent",
    ]

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        return await self.generate_response(
            "You are the Cursor-style coding agent — read the repo, edit files, and run commands.",
            message,
        )


class AntigravityAgent(BaseAgent):
    name = "Antigravity Agent"
    description = "Multi-agent orchestration runtime with tools and sub-agent delegation"
    tools = [
        "invoke_agent",
        "parallel_invoke_agents",
        "list_agents",
        "deep_research",
        "recall_notes",
        "store_note",
    ]

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        return await self.generate_response(
            "You are the Antigravity orchestrator — plan, delegate, and merge specialist outputs.",
            message,
        )


class CopilotAgent(BaseAgent):
    name = "Copilot Agent"
    description = "Inline pair-programming assists, explanations, and quick code patches"
    tools = ["read_file", "edit_file", "run_python", "run_shell_command"]

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        return await self.generate_response(
            "You are Copilot-style assist — short, precise coding help with minimal diffs.",
            message,
        )


class NotebookLmAgent(BaseAgent):
    name = "NotebookLM Agent"
    description = "Grounded answers from PDFs, notes, and uploaded sources"
    tools = [
        "read_pdf",
        "read_file",
        "deep_research",
        "search_papers",
        "recall_notes",
        "store_note",
    ]

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        ctx = context or {}
        if "pdf" in message.lower():
            result = await run_tool("read_pdf", ctx, path=message)
            return format_tool_results([result])
        return await self.generate_response(
            "You are NotebookLM-style — cite sources from documents and notes only.",
            message,
        )


class CloudCodeAgent(BaseAgent):
    name = "Cloud Code Agent"
    description = "Cloud sandbox execution — scripts, shells, and remote dev tasks"
    tools = ["run_shell_command", "run_python", "write_file", "read_file", "list_directory"]

    async def process(self, message: str, context: Optional[Dict] = None) -> str:
        return await self.generate_response(
            "You are Cloud Code — run isolated commands and scripts safely in the sandbox.",
            message,
        )
