"""Vercel entrypoint for the existing FPDS FastAPI application."""

from __future__ import annotations

import os
import sys
from importlib import import_module
from pathlib import Path


# Vercel instances are request-scoped. Collection automation belongs in the
# long-running worker boundary and must never start inside this deployment.
if os.getenv("VERCEL"):
    os.environ["FPDS_AUTOMATION_SCHEDULER_ENABLED"] = "false"

# The API remains an independently runnable package under `api/service`.
# Vercel installs the root project, so expose that source root without copying
# or forking the application package.
api_service_root = Path(__file__).resolve().parent / "api" / "service"
sys.path.insert(0, str(api_service_root))

app = import_module("api_service.main").app

__all__ = ["app"]
