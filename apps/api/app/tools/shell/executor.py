"""Shell execution tools — run commands and Python code in a subprocess."""
import asyncio
import os
import sys
from pathlib import Path

from ..base import BaseTool, ToolParameter, ToolResult
from .workspace import is_shell_command_allowed, resolve_workspace_path, workspace_root


class RunCommandTool(BaseTool):
    name = "run_shell_command"
    description = (
        "Run a shell command inside the workspace sandbox and return stdout/stderr. "
        "Antigravity parity for run_command."
    )
    category = "shell"
    parameters = [
        ToolParameter(name="command", type="string", description="Shell command to execute"),
        ToolParameter(
            name="cwd",
            type="string",
            description="Working directory relative to workspace (optional)",
            required=False,
        ),
        ToolParameter(
            name="timeout",
            type="integer",
            description="Timeout in seconds (default 30)",
            required=False,
            default=30,
        ),
        ToolParameter(
            name="env",
            type="string",
            description="Optional env vars as KEY=VALUE pairs separated by commas",
            required=False,
        ),
    ]

    async def execute(
        self,
        command: str,
        cwd: str = None,
        timeout: int = 30,
        env: str = None,
    ) -> ToolResult:
        allowed, reason = is_shell_command_allowed(command)
        if not allowed:
            return self.fail(reason or "Command not allowed")

        try:
            workdir = str(resolve_workspace_path(cwd) if cwd else workspace_root())
            if not Path(workdir).is_dir():
                workdir = str(workspace_root())
        except Exception:
            workdir = str(workspace_root())

        child_env = os.environ.copy()
        if env:
            for pair in env.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    child_env[key.strip()] = value.strip()

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
                env=child_env,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                return self.fail(f"Command timed out after {timeout}s")

            out = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace")
            return self.ok({
                "command": command,
                "cwd": workdir,
                "returncode": proc.returncode,
                "stdout": out[:5000],
                "stderr": err[:2000],
                "stdout_truncated": len(out) > 5000,
                "stderr_truncated": len(err) > 2000,
                "success": proc.returncode == 0,
            })
        except Exception as e:
            return self.fail(str(e))


class RunPythonTool(BaseTool):
    name = "run_python"
    description = "Execute a Python code snippet and return output"
    category = "shell"
    parameters = [
        ToolParameter(name="code", type="string", description="Python code to execute"),
        ToolParameter(name="timeout", type="integer", description="Timeout in seconds (default 15)", required=False, default=15),
    ]

    async def execute(self, code: str, timeout: int = 15) -> ToolResult:
        import tempfile, os
        # Write to temp file and run with venv python
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            python = sys.executable
            proc = await asyncio.create_subprocess_exec(
                python, tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                return self.fail(f"Python execution timed out after {timeout}s")

            return self.ok({
                "returncode": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace")[:5000],
                "stderr": stderr.decode("utf-8", errors="replace")[:2000],
                "success": proc.returncode == 0,
            })
        finally:
            os.unlink(tmp_path)
