#!/usr/bin/env bash
# Sync packages/daffodil-kit/VERSION into pyproject.toml, __init__.py, and native/Cargo.toml
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"

if [[ -z "$VERSION" ]]; then
  echo "VERSION file is empty" >&2
  exit 1
fi

python3 - "$ROOT" "$VERSION" <<'PY'
import pathlib
import re
import sys

root, version = sys.argv[1], sys.argv[2]

pyproject = pathlib.Path(root) / "pyproject.toml"
text = pyproject.read_text()
text = re.sub(r'^version = ".*"$', f'version = "{version}"', text, count=1, flags=re.M)
pyproject.write_text(text)

init_py = pathlib.Path(root) / "daffodil_kit" / "__init__.py"
init_text = init_py.read_text()
init_text = re.sub(r'^__version__ = ".*"$', f'__version__ = "{version}"', init_text, count=1, flags=re.M)
init_py.write_text(init_text)

cargo = pathlib.Path(root) / "native" / "Cargo.toml"
cargo_text = cargo.read_text()
cargo_text = re.sub(r'^version = ".*"$', f'version = "{version}"', cargo_text, count=1, flags=re.M)
cargo.write_text(cargo_text)

print(f"Synced version {version}")
PY
