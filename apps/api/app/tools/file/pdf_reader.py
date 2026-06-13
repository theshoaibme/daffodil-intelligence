"""General-purpose fast PDF reader tool."""

from __future__ import annotations

from pathlib import Path

from ..base import BaseTool, ToolParameter, ToolResult
from ...lib.pdf_reader import read_pdf_fast


class ReadPdfTool(BaseTool):
    name = "read_pdf"
    description = (
        "Read text from any PDF or text file (cached sidecar for speed). "
        "Use for documents, routines, syllabi, notices — not only department routines. "
        "Optional query filters matching lines; page_start/page_end for partial reads."
    )
    category = "file"
    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="Absolute or relative path to a .pdf or .txt file",
        ),
        ToolParameter(
            name="query",
            type="string",
            description="Optional keyword — return only matching lines",
            required=False,
        ),
        ToolParameter(
            name="page_start",
            type="integer",
            description="First PDF page (1-based, optional)",
            required=False,
        ),
        ToolParameter(
            name="page_end",
            type="integer",
            description="Last PDF page (1-based, optional)",
            required=False,
        ),
        ToolParameter(
            name="max_chars",
            type="integer",
            description="Max characters to return (default 8000)",
            required=False,
            default=8000,
        ),
    ]

    async def execute(
        self,
        path: str,
        query: str = None,
        page_start: int = None,
        page_end: int = None,
        max_chars: int = 8000,
        **kwargs,
    ) -> ToolResult:
        if not path or not str(path).strip():
            return self.fail("path is required")

        resolved = Path(path).expanduser()
        if not resolved.is_file():
            return self.fail(f"File not found: {path}")

        result = read_pdf_fast(
            resolved,
            query=query.strip() if query else None,
            page_start=page_start,
            page_end=page_end,
            max_chars=int(max_chars or 8000),
        )
        if result.get("error"):
            err = result["error"]
            if err == "not_found":
                return self.fail(f"File not found: {path}")
            if err == "empty_document":
                return self.fail(f"No extractable text in: {path}")
            return self.fail(str(err))

        return self.ok(result)
