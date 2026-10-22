"""Debug entry: shows the REAL import error on the page."""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mangum import Mangum  # noqa: E402
    from app.main import app as fastapi_app  # noqa: E402

    app = Mangum(fastapi_app, lifespan="off")
    handler = app
except Exception:
    def handler(event, context=None):  # noqa: F811
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/plain; charset=utf-8"},
            "body": "IMPORT ERROR (asli waja):\n\n" + traceback.format_exc(),
        }
