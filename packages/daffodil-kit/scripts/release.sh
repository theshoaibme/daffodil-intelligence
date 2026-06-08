#!/usr/bin/env bash
# Bump CopyCat Kit version and prepare release tag
# Usage: bash scripts/release.sh 0.1.1
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NEW="${1:-}"

if [[ -z "$NEW" ]]; then
  echo "Usage: $0 <version>   e.g. 0.1.1" >&2
  echo "Current: $(tr -d '[:space:]' < "$ROOT/VERSION")" >&2
  exit 1
fi

if ! [[ "$NEW" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must be semver: X.Y.Z" >&2
  exit 1
fi

echo "$NEW" > "$ROOT/VERSION"
bash "$ROOT/scripts/sync-version.sh"

echo ""
echo "Version bumped to $NEW"
echo "Next:"
echo "  git add packages/daffodil-kit/VERSION packages/daffodil-kit/pyproject.toml \\"
echo "          packages/daffodil-kit/daffodil_kit/__init__.py packages/daffodil-kit/native/Cargo.toml"
echo "  git commit -m \"chore(copycat): release $NEW\""
echo "  git tag copycat-v$NEW"
echo "  git push origin HEAD --tags"
