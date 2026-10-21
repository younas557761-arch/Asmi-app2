"""School Builder core: turn natural-language commands into typed,
validated, allowlisted action plans. Never executes arbitrary code or SQL.
"""

import json
import re

from sqlalchemy.orm import Session

from app.models import (
    AcademicYear,
    FeeCategory,
    SchoolClass,
    Student,
    Subject,
    Teacher,
)

# ---------------- Action registry (the ONLY actions the builder may plan) ----------------

ACTIONS = {
    "create_class": {"params": ["name"], "description": "Create a new class in the current academic year"},
    "create_subject": {"params": ["name"], "description": "Create a subject"},
    "create_fee_category": {"params": ["name", "amount"], "description": "Create a fee category"},
    "create_academic_year": {"params": ["name", "start_date", "end_date"], "description": "Create an academic year"},
    "enroll_student": {"params": ["first_name", "admission_number"], "description": "Enrol a student"},
    "add_teacher": {"params": ["first_name", "employee_number"], "description": "Add a teacher"},
}


def _cmd(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


# ---------------- Intent parsing (rule engine) ----------------

def parse_command(command: str) -> dict:
    """Convert a plain-language command into a typed action. Returns
    {"action": ..., "params": {...}, "confidence": "high|medium|low"}
    or {"action": None, "reason": ...}."""
    text = _cmd(command)

    m = re.search(r"(?:add|create)\s+(?:a\s+)?(?:new\s+)?(?:class|grade)\s+([a-z0-9\- ]{1,40})", text)
    if m:
        return {"action": "create_class", "params": {"name": m.group(1).strip().title()}, "confidence": "high"}

    m = re.search(r"(?:add|create)\s+(?:a\s+)?(?:new\s+)?subject\s+([a-z0-9\- ]{1,60})", text)
    if m:
        return {"action": "create_subject", "params": {"name": m.group(1).strip().title()}, "confidence": "high"}

    m = re.search(r"(?:add|create)\s+(?:a\s+)?(?:monthly\s+)?fee\s+category\s+([a-z0-9\- ]{1,60})\s+(?:of|for|rs\.?|pkr)?\s*(\d+)?", text)
    if m:
        params = {"name": m.group(1).strip().title(), "amount": int(m.group(2)) if m.group(2) else 0}
        return {"action": "create_fee_category", "params": params, "confidence": "high" if m.group(2) else "medium"}

    m = re.search(r"academic year\s+(\d{4}[-/]\d{2,4})", text)
    if m:
        name = m.group(1).replace("/", "-")
        try:
            start_year = int(name.split("-")[0])
        except ValueError:
            start_year = None
        if start_year:
            return {
                "action": "create_academic_year",
                "params": {"name": name, "start_date": f"{start_year}-04-01", "end_date": f"{start_year + 1}-03-31"},
                "confidence": "medium",
            }

    return {"action": None, "reason": "I could not map this command to a supported action yet.", "confidence": "low"}


# ---------------- Validation ----------------

def validate_plan(db: Session, school_id: str, action: str, params: dict) -> list[str]:
    """Return a list of human-readable problems. Empty list = valid."""
    problems: list[str] = []
    if action not in ACTIONS:
        return [f"Unknown action '{action}'."]
    for key in ACTIONS[action]["params"]:
        if key not in params or params[key] in (None, ""):
            problems.append(f"Missing required parameter: {key}")

    if action == "create_class":
        year = (
            db.query(AcademicYear)
            .filter(AcademicYear.school_id == school_id, AcademicYear.is_current.is_(True))
            .first()
        )
        if not year:
            problems.append("No current academic year. Create and activate one first.")
        elif params.get("name"):
            exists = (
                db.query(SchoolClass)
                .filter(
                    SchoolClass.school_id == school_id,
                    SchoolClass.academic_year_id == year.id,
                    SchoolClass.name == params["name"],
                )
                .first()
            )
            if exists:
                problems.append(f"Class '{params['name']}' already exists this year.")

    if action == "create_subject" and params.get("name"):
        if db.query(Subject).filter(Subject.school_id == school_id, Subject.name == params["name"]).first():
            problems.append(f"Subject '{params['name']}' already exists.")

    if action == "create_fee_category" and params.get("name"):
        if db.query(FeeCategory).filter(FeeCategory.school_id == school_id, FeeCategory.name == params["name"]).first():
            problems.append(f"Fee category '{params['name']}' already exists.")

    if action == "enroll_student" and params.get("admission_number"):
        if (
            db.query(Student)
            .filter(Student.school_id == school_id, Student.admission_number == params["admission_number"])
            .first()
        ):
            problems.append(f"Admission number '{params['admission_number']}' is already used.")

    if action == "add_teacher" and params.get("employee_number"):
        if (
            db.query(Teacher)
            .filter(Teacher.school_id == school_id, Teacher.employee_number == params["employee_number"])
            .first()
        ):
            problems.append(f"Employee number '{params['employee_number']}' is already used.")

    return problems


# ---------------- Apply (typed, safe) ----------------

def apply_action(db: Session, school_id: str, user_id: str, action: str, params: dict) -> str:
    """Apply a single validated action. Only registry actions reach here."""
    if action == "create_class":
        year = (
            db.query(AcademicYear)
            .filter(AcademicYear.school_id == school_id, AcademicYear.is_current.is_(True))
            .first()
        )
        row = SchoolClass(school_id=school_id, academic_year_id=year.id, name=params["name"])
        db.add(row)
        return f"Class '{params['name']}' created."
    if action == "create_subject":
        db.add(Subject(school_id=school_id, name=params["name"]))
        return f"Subject '{params['name']}' created."
    if action == "create_fee_category":
        db.add(
            FeeCategory(
                school_id=school_id,
                name=params["name"],
                default_amount=params.get("amount", 0),
                frequency="monthly",
            )
        )
        return f"Fee category '{params['name']}' created."
    if action == "create_academic_year":
        db.add(
            AcademicYear(
                school_id=school_id,
                name=params["name"],
                start_date=params["start_date"],
                end_date=params["end_date"],
                is_current=False,
            )
        )
        return f"Academic year '{params['name']}' created."
    if action == "enroll_student":
        db.add(
            Student(
                school_id=school_id,
                first_name=params["first_name"],
                admission_number=params["admission_number"],
            )
        )
        return f"Student '{params['first_name']}' enrolled."
    if action == "add_teacher":
        db.add(
            Teacher(
                school_id=school_id,
                first_name=params["first_name"],
                employee_number=params["employee_number"],
            )
        )
        return f"Teacher '{params['first_name']}' added."
    raise ValueError(f"Action '{action}' is not in the registry.")


def plan_to_json(parsed: dict, problems: list[str]) -> str:
    return json.dumps(
        {
            "action": parsed.get("action"),
            "params": parsed.get("params", {}),
            "confidence": parsed.get("confidence", "low"),
            "validation": {"ok": not problems, "problems": problems},
        }
    )
