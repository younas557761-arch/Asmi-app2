import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.core.database import Base
from app.core.security import utcnow


def _uuid() -> str:
    return str(uuid.uuid4())


class AIActionPlan(Base):
    """A proposed set of typed, validated actions produced from a command."""

    __tablename__ = "ai_action_plans"

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    command = Column(Text, nullable=False)
    plan_json = Column(Text, nullable=False)  # typed actions, allowlisted only
    status = Column(String(20), default="pending", nullable=False)  # pending/approved/rejected/applied
    engine = Column(String(20), default="rule", nullable=False)  # rule/ai
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class AIActionApproval(Base):
    """One approval record per applied plan (who approved, when)."""

    __tablename__ = "ai_action_approvals"

    id = Column(String(36), primary_key=True, default=_uuid)
    plan_id = Column(String(36), ForeignKey("ai_action_plans.id"), nullable=False, index=True)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
