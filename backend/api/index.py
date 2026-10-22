"""Vercel entry — FastAPI preset serves this ASGI app directly."""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.main import app  # FastAPI ASGI app
except Exception:
    _tb = traceback.format_exc()

    async def app(scope, receive, send):  # noqa: F811
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/plain; charset=utf-8"]],
        })
        await send({
            "type": "http.response.body",
            "body": ("IMPORT ERROR (asli waja):\n\n" + _tb).encode(),
        })
