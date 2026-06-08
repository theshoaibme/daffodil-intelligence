#!/usr/bin/env bash
# Build Rust capture extension (Linux deps required once):
#   Debian/Kali: sudo apt install libdbus-1-dev libxcb1-dev libxrandr-dev pkg-config
set -euo pipefail
cd "$(dirname "$0")/.."
pip install maturin
maturin develop --release -m native/Cargo.toml
echo "Rust backend installed — verify: python -c 'import daffodil_kit_native'"
