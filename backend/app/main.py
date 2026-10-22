from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import (
    announcements,
    assistant,
    attendance,
    audit,
    auth,
    builder,
    classes,
    dashboard,
    exams,
    fees,
    onboarding,
    people,
    reports,
    schools,
    students,
    teachers,
    verify,
)
from app.core.config import settings
from app.core.database import Base, engine
import app.models  # noqa: F401  (register all tables in metadata)

app = FastAPI(title="ASMI API", version="0.4.4", docs_url="/docs", openapi_url="/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "asmi-api", "version": "0.4.4"}


@app.get("/db-test")
def db_test():
    """Creates all tables (if missing) and verifies a real table."""
    import traceback

    try:
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            conn.execute(text("SELECT count(*) FROM users"))
        return {"db": "CONNECTED + TABLES READY ✅ — ab register karein"}
    except Exception:
        return {"db": "FAILED ❌", "error": traceback.format_exc()[-800:]}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(verify.router, prefix="/api/v1")
app.include_router(schools.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(classes.router, prefix="/api/v1")
app.include_router(teachers.router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(fees.router, prefix="/api/v1")
app.include_router(exams.router, prefix="/api/v1")
app.include_router(people.router, prefix="/api/v1")
app.include_router(announcements.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(builder.router, prefix="/api/v1")
app.include_router(assistant.router, prefix="/api/v1")
app.include_router(onboarding.router, prefix="/api/v1")
