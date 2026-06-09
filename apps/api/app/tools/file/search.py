"""File search tools — Antigravity parity for search_directory and find_file."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from ..base import BaseTool, ToolParameter, ToolResult
from ..shell.workspace import resolve_workspace_path


class SearchDirectoryTool(BaseTool):
    name = "search_directory"
    description = "Search file contents under a directory (grep-style)."
    category = "file"
    parameters = [
        ToolParameter(name="path", type="string", description="Directory to search"),
        ToolParameter(name="pattern", type="string", description="Text or regex pattern to find"),
        ToolParameter(
            name="glob",
            type="string",
            description="Optional filename glob e.g. '*.py'",
            required=False,
        ),
        ToolParameter(
            name="max_matches",
            type="integer",
            description="Max matches to return (default 50)",
            required=False,
            default=50,
        ),
    ]

    async def execute(
        self,
        path: str,
        pattern: str,
        glob: str = None,
        max_matches: int = 50,
    ) -> ToolResult:
        try:
            root = resolve_workspace_path(path, must_exist=True)
            if not root.is_dir():
                return self.fail(f"Not a directory: {path}")

            regex = re.compile(pattern)
            matches: list[dict] = []
            for file_path in root.rglob("*"):
                if not file_path.is_file():
                    continue
                if glob and not fnmatch.fnmatch(file_path.name, glob):
                    continue
                try:
                    text = file_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                for line_no, line in enumerate(text.splitlines(), start=1):
                    if regex.search(line):
                        matches.append(
                            {
                                "file": str(file_path),
                                "line": line_no,
                                "text": line.strip()[:300],
                            }
                        )
                        if len(matches) >= max_matches:
                            break
                if len(matches) >= max_matches:
                    break

            return self.ok(
                {
                    "path": str(root),
                    "pattern": pattern,
                    "matches": matches,
                    "count": len(matches),
                }
            )
        except Exception as e:
            return self.fail(str(e))


class FindFileTool(BaseTool):
    name = "find_file"
    description = "Find files by name pattern under a directory."
    category = "file"
    parameters = [
        ToolParameter(name="path", type="string", description="Root directory"),
        ToolParameter(name="name", type="string", description="Filename glob e.g. '*.py' or 'config.json'"),
        ToolParameter(
            name="max_results",
            type="integer",
            description="Max files to return (default 100)",
            required=False,
            default=100,
        ),
    ]

    async def execute(self, path: str, name: str, max_results: int = 100) -> ToolResult:
        try:
            root = resolve_workspace_path(path, must_exist=True)
            if not root.is_dir():
                return self.fail(f"Not a directory: {path}")

            files: list[str] = []
            for file_path in root.rglob("*"):
                if not file_path.is_file():
                    continue
                if fnmatch.fnmatch(file_path.name, name):
                    files.append(str(file_path))
                if len(files) >= max_results:
                    break

            return self.ok(
                {
                    "path": str(root),
                    "pattern": name,
                    "files": files,
                    "count": len(files),
                }
            )
        except Exception as e:
            return self.fail(str(e))


class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Apply a targeted text replacement in a file (patch-style edit)."
    category = "file"
    parameters = [
        ToolParameter(name="path", type="string", description="File path to edit"),
        ToolParameter(name="old_text", type="string", description="Exact text to replace"),
        ToolParameter(name="new_text", type="string", description="Replacement text"),
        ToolParameter(
            name="replace_all",
            type="boolean",
            description="Replace all occurrences (default false)",
            required=False,
            default=False,
        ),
    ]

    async def execute(
        self,
        path: str,
        old_text: str,
        new_text: str,
        replace_all: bool = False,
    ) -> ToolResult:
        try:
            file_path = resolve_workspace_path(path, must_exist=True)
            if not file_path.is_file():
                return self.fail(f"Not a file: {path}")

            content = file_path.read_text(encoding="utf-8")
            if old_text not in content:
                return self.fail("old_text not found in file")

            count = content.count(old_text)
            if replace_all:
                updated = content.replace(old_text, new_text)
            else:
                updated = content.replace(old_text, new_text, 1)

            file_path.write_text(updated, encoding="utf-8")
            replacements = count if replace_all else 1
            return self.ok(
                {
                    "path": str(file_path),
                    "replacements": replacements,
                    "bytes_written": len(updated.encode("utf-8")),
                }
            )
        except Exception as e:
            return self.fail(str(e))
