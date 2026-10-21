from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_school
from app.core.database import get_db
from app.models import School
from app.schemas.ai import AssistantAskRequest, AssistantAskResponse
from app.services import assistant as assistant_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/suggestions")
def suggestions():
    return {"items": assistant_service.SUGGESTIONS}


@router.post("/ask", response_model=AssistantAskResponse)
def ask(
    data: AssistantAskRequest,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    """Answer a school question using live database figures (rule engine).
    Works with no external AI provider configured."""
    result = assistant_service.answer(db, school, data.question)
    return AssistantAskResponse(text=result["text"], figures=result["figures"], engine="rule")
