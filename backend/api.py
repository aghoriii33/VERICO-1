"""Vercel ASGI entry point for the FastAPI backend."""

import os
import sys


sys.path.insert(0, os.path.dirname(__file__))

from app.main import app  # noqa: E402,F401

# Keep an explicit handler alias for Vercel's Python runtime.
handler = app
