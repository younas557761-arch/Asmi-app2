from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    announcements,
    attendance,
    audit,
    auth,
    classes,
    dashboard,
    exams,
    fees,
    people,
    reports,
    schools,
    students,
    teachers,
    verify,
)
from app.core.config import settings
from app.core.database import Base, engine

# create_all is used for the dev schema. Alembic migrations land in a later phase.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ASMI API", version="0.3.0", docs_url="/docs", openapi_url="/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "asmi-api", "version": "0.3.0"}


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
