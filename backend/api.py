"""
Vercel serverless function entry point for FastAPI backend
"""
from app.main import app

# Export the FastAPI app for Vercel to use as ASGI handler
handler = app
