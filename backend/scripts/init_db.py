"""Dev helper: create all tables. Alembic replaces this in Phase 2."""
from app.core.database import Base, engine
import app.models  # noqa: F401

Base.metadata.create_all(bind=engine)
print("database schema created")
