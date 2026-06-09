"""Guard against syntax regressions in daemon module."""

import py_compile
from pathlib import Path


def test_daemon_module_compiles():
    daemon_py = Path(__file__).resolve().parents[1] / "daffodil_kit" / "daemon.py"
    py_compile.compile(str(daemon_py), doraise=True)
