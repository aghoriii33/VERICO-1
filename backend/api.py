"""
Vercel serverless function entry point for FastAPI backend
Handles ASGI requests from Vercel's Python runtime
"""
import os
import sys

# Ensure the app package is importable
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.main import app
    
    # Vercel's Python runtime expects an ASGI app
    # This is the entry point for serverless functions
    handler = app
    
except Exception as e:
    import traceback
    print(f"Error initializing FastAPI app: {e}")
    traceback.print_exc()
    
    # Fallback ASGI app for debugging
    async def fallback_app(scope, receive, send):
        await send({
            'type': 'http.response.start',
            'status': 500,
            'headers': [[b'content-type', b'application/json']],
        })
        await send({
            'type': 'http.response.body',
            'body': b'{"error": "Backend initialization failed"}',
        })
    
    handler = fallback_app
