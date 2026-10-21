import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.models import AIActionApproval, AIActionPlan, School, User
from app.schemas.ai import ApproveRequest, ApproveResponse, PlanRequest, PlanResponse
from app.services import builder as builder_service
from app.services.audit import write_audit

router = APIRouter(prefix="/builder", tags=["builder"])


def _to_response(plan: AIActionPlan) -> PlanResponse:
    return PlanResponse(
        id=plan.id,
        status=plan.status,
        engine=plan.engine,
        command=plan.command,
        plan=json.loads(plan.plan_json),
    )


@router.post("/plan", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    data: PlanRequest,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Convert a natural-language command into a typed, validated plan.
    Nothing is applied here — the owner must review and approve."""
    parsed = builder_service.parse_command(data.command)
    if not parsed.get("action"):
        plan = AIActionPlan(
            school_id=school.id,
            command=data.command,
            plan_json=builder_service.plan_to_json(parsed, [parsed.get("reason", "Unrecognised command")]),
            status="rejected",
            engine="rule",
            created_by=user.id,
        )
        db.add(plan)
        write_audit(db, school.id, user.id, "builder.plan_rejected", data.command[:120], source="ai_builder")
        db.commit()
        return _to_response(plan)

    problems = builder_service.validate_plan(db, school.id, parsed["action"], parsed["params"])
    plan = AIActionPlan(
        school_id=school.id,
        command=data.command,
        plan_json=builder_service.plan_to_json(parsed, problems),
        status="pending" if not problems else "rejected",
        engine="rule",
        created_by=user.id,
    )
    db.add(plan)
    write_audit(
        db, school.id, user.id,
        "builder.plan_created",
        f"{parsed['action']} ({'valid' if not problems else 'invalid'})",
        source="ai_builder",
    )
    db.commit()
    return _to_response(plan)


@router.get("/plans", response_model=dict)
def list_plans(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    items = (
        db.query(AIActionPlan)
        .filter(AIActionPlan.school_id == school.id)
        .order_by(AIActionPlan.created_at.desc())
        .limit(50)
        .all()
    )
    return {"items": [_to_response(p) for p in items], "total": len(items)}


@router.post("/approve", response_model=ApproveResponse)
def approve_plan(
    data: ApproveRequest,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apply a pending plan after owner approval. Idempotent: approving an
    already-applied plan returns the stored result instead of re-applying."""
    plan = db.get(AIActionPlan, data.plan_id)
    if not plan or plan.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    if plan.status == "applied":
        return ApproveResponse(plan_id=plan.id, status="applied", result="Already applied.")
    if plan.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Plan is {plan.status} and cannot be approved")

    body = json.loads(plan.plan_json)
    action, params = body["action"], body["params"]
    # Re-validate at approval time — data may have changed since planning
    problems = builder_service.validate_plan(db, school.id, action, params)
    if problems:
        plan.status = "rejected"
        write_audit(db, school.id, user.id, "builder.plan_revalidated_failed", "; ".join(problems), source="ai_builder")
        db.commit()
        raise HTTPException(status.HTTP_409_CONFLICT, "; ".join(problems))

    result = builder_service.apply_action(db, school.id, user.id, action, params)
    plan.status = "applied"
    db.add(AIActionApproval(plan_id=plan.id, school_id=school.id, approved_by=user.id))
    write_audit(
        db, school.id, user.id, "builder.plan_applied",
        f"{action}: {json.dumps(params)[:200]}",
        severity="warning", source="ai_builder",
    )
    db.commit()
    return ApproveResponse(plan_id=plan.id, status="applied", result=result)


@router.post("/{plan_id}/reject", response_model=ApproveResponse)
def reject_plan(
    plan_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.get(AIActionPlan, plan_id)
    if not plan or plan.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    if plan.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Plan is {plan.status} and cannot be rejected")
    plan.status = "rejected"
    write_audit(db, school.id, user.id, "builder.plan_rejected", plan.command[:120], source="ai_builder")
    db.commit()
    return ApproveResponse(plan_id=plan.id, status="rejected", result="Plan rejected.")
