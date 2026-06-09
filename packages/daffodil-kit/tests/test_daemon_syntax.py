"""Guard against syntax regressions in daemon module."""

import importlib
import py_compile
import sys
from pathlib import Path


def test_daemon_module_compiles():
    daemon_py = Path(__file__).resolve().parents[1] / "daffodil_kit" / "daemon.py"
    py_compile.compile(str(daemon_py), doraise=True)


def test_package_import_defers_display_modules():
    sys.modules.pop("daffodil_kit", None)
    sys.modules.pop("daffodil_kit.cli", None)
    sys.modules.pop("daffodil_kit.daemon", None)
    sys.modules.pop("daffodil_kit.keyboard", None)
    sys.modules.pop("daffodil_kit.mouse", None)
    sys.modules.pop("daffodil_kit.screen", None)

    importlib.import_module("daffodil_kit")

    assert "daffodil_kit.keyboard" not in sys.modules
    assert "daffodil_kit.mouse" not in sys.modules
    assert "daffodil_kit.screen" not in sys.modules


def test_cli_import_defers_display_modules():
    sys.modules.pop("daffodil_kit.cli", None)
    sys.modules.pop("daffodil_kit.daemon", None)
    sys.modules.pop("daffodil_kit.keyboard", None)
    sys.modules.pop("daffodil_kit.mouse", None)
    sys.modules.pop("daffodil_kit.screen", None)

    importlib.import_module("daffodil_kit.cli")

    assert "daffodil_kit.daemon" not in sys.modules
    assert "daffodil_kit.keyboard" not in sys.modules
    assert "daffodil_kit.mouse" not in sys.modules
    assert "daffodil_kit.screen" not in sys.modules
