"""Vercel serverless entry for the ASMI backend."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangum import Mangum  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

# Vercel's Python runtime looks for a variable named `app`.
app = Mangum(fastapi_app, lifespan="off")
handler = app
