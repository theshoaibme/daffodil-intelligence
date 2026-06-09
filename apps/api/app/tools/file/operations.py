"""File system tools — read, write, list, delete files."""
import os
from pathlib import Path
from ..base import BaseTool, ToolParameter, ToolResult


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read contents of a file on the filesystem"
    category = "file"
    parameters = [
        ToolParameter(name="path", type="string", description="Absolute or relative path to file"),
        ToolParameter(name="max_chars", type="integer", description="Max chars to return (default 5000)", required=False, default=5000),
    ]

    async def execute(self, path: str, max_chars: int = 5000) -> ToolResult:
        try:
            p = Path(path)
            if not p.exists():
                return self.fail(f"File not found: {path}")
            if not p.is_file():
                return self.fail(f"Not a file: {path}")
            text = p.read_text(encoding="utf-8", errors="replace")
            truncated = len(text) > max_chars
            return self.ok({
                "path": str(p.resolve()),
                "content": text[:max_chars],
                "truncated": truncated,
                "total_chars": len(text),
                "size_bytes": p.stat().st_size,
            })
        except Exception as e:
            return self.fail(str(e))


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write or append content to a file"
    category = "file"
    parameters = [
        ToolParameter(name="path", type="string", description="Path to write to"),
        ToolParameter(name="content", type="string", description="Content to write"),
        ToolParameter(name="mode", type="string", description="'write' (overwrite) or 'append' (default 'write')", required=False, default="write"),
    ]

    async def execute(self, path: str, content: str, mode: str = "write") -> ToolResult:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            file_mode = "w" if mode == "write" else "a"
            p.write_text(content, encoding="utf-8") if file_mode == "w" else open(p, "a", encoding="utf-8").write(content)
            return self.ok({"path": str(p.resolve()), "bytes_written": len(content.encode()), "mode": mode})
        except Exception as e:
            return self.fail(str(e))


class ListDirTool(BaseTool):
    name = "list_directory"
    description = "List files and directories at a given path"
    category = "file"
    parameters = [
        ToolParameter(name="path", type="string", description="Directory path to list"),
        ToolParameter(name="recursive", type="boolean", description="List recursively (default false)", required=False, default=False),
    ]

    async def execute(self, path: str, recursive: bool = False) -> ToolResult:
        try:
            p = Path(path)
            if not p.exists():
                return self.fail(f"Directory not found: {path}")
            if not p.is_dir():
                return self.fail(f"Not a directory: {path}")

            entries = []
            if recursive:
                for item in sorted(p.rglob("*"))[:200]:
                    entries.append({
                        "name": item.name,
                        "path": str(item.relative_to(p)),
                        "type": "dir" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    })
            else:
                for item in sorted(p.iterdir()):
                    entries.append({
                        "name": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    })

            return self.ok({"path": str(p.resolve()), "entries": entries, "count": len(entries)})
        except Exception as e:
            return self.fail(str(e))


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file (NOT directories — use with caution)"
    category = "file"
    parameters = [
        ToolParameter(name="path", type="string", description="Path to file to delete"),
    ]

    async def execute(self, path: str) -> ToolResult:
        try:
            p = Path(path)
            if not p.exists():
                return self.fail(f"File not found: {path}")
            if not p.is_file():
                return self.fail("Can only delete files, not directories")
            p.unlink()
            return self.ok({"deleted": str(p.resolve())})
        except Exception as e:
            return self.fail(str(e))
