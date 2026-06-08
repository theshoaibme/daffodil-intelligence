"""Shared pytest fixtures/config for the Daffodil API test suite."""

import os
import sys
from pathlib import Path

# Ensure the API package (``app``) is importable: tests run from apps/api.
API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

# University-data mocks only; auth always requires real register/login + JWT.
os.environ.setdefault("USE_MOCK_DATA", "true")
