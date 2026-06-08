"""Shell execution tools — run commands and Python code in a subprocess."""
import asyncio
import sys
from ..base import BaseTool, ToolParameter, ToolResult


class RunCommandTool(BaseTool):
    name = "run_shell_command"
    description = "Run a shell command and return stdout/stderr"
    category = "shell"
    parameters = [
        ToolParameter(name="command", type="string", description="Shell command to execute"),
        ToolParameter(name="cwd", type="string", description="Working directory (optional)", required=False),
        ToolParameter(name="timeout", type="integer", description="Timeout in seconds (default 30)", required=False, default=30),
    ]

    async def execute(self, command: str, cwd: str = None, timeout: int = 30) -> ToolResult:
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                return self.fail(f"Command timed out after {timeout}s")

            return self.ok({
                "command": command,
                "returncode": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace")[:5000],
                "stderr": stderr.decode("utf-8", errors="replace")[:2000],
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
