from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, schools, students
from app.core.config import settings
from app.core.database import Base, engine

# Phase 1 uses create_all for the dev schema. Alembic migrations land in Phase 2.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ASMI API", version="0.1.0", docs_url="/docs", openapi_url="/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "asmi-api"}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(schools.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
