"""Template catalogue for workspace onboarding.

Templates are starting configurations, not restrictions: any module can be
switched on or off later and any class/subject can be added or removed.
"""

MODULES = [
    {"key": "students", "name": "Student management", "desc": "Admissions, profiles, class assignment, import and export"},
    {"key": "teachers", "name": "Teacher & staff management", "desc": "Profiles, departments, subjects, workload"},
    {"key": "classes", "name": "Classes & subjects", "desc": "Grades, sections, subjects and promotion"},
    {"key": "attendance", "name": "Attendance", "desc": "Daily marking, summaries and exports"},
    {"key": "timetable", "name": "Timetable", "desc": "Weekly periods, rooms, conflict checks and printing"},
    {"key": "fees", "name": "Fees & finance", "desc": "Categories, invoices, payments, waivers and balances"},
    {"key": "exams", "name": "Examinations & results", "desc": "Schedules, marks, grading and report cards"},
    {"key": "portal", "name": "Parent portal", "desc": "Guardian accounts, linked children and statements"},
    {"key": "communication", "name": "Communication", "desc": "Announcements, notifications and message templates"},
    {"key": "reports", "name": "Reports & analytics", "desc": "Enrollment, attendance, finance and performance reports"},
]

GRADE_SETS = {
    "primary": ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"],
    "secondary": ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10"],
    "higher_secondary": ["Grade 11", "Grade 12"],
    "international": ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Stage 6"],
    "private": ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"],
    "public": ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"],
    "small": ["Class A", "Class B", "Class C"],
    "multi_campus": ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"],
}

DEFAULT_SUBJECTS = ["English", "Urdu", "Mathematics", "Science", "Social Studies"]

TEMPLATES = [
    {
        "key": "primary",
        "name": "Primary school",
        "desc": "Grades 1-5 with class teachers, monthly fees and term exams.",
        "grades": GRADE_SETS["primary"],
        "modules": [m["key"] for m in MODULES],
        "fee_categories": [
            {"name": "Monthly Tuition", "amount": 3000, "frequency": "monthly"},
            {"name": "Admission Fee", "amount": 5000, "frequency": "one_time"},
            {"name": "Exam Fee", "amount": 500, "frequency": "term"},
        ],
    },
    {
        "key": "secondary",
        "name": "Secondary school",
        "desc": "Grades 6-10 with subject teachers, exams and result publication.",
        "grades": GRADE_SETS["secondary"],
        "modules": [m["key"] for m in MODULES],
        "fee_categories": [
            {"name": "Monthly Tuition", "amount": 4000, "frequency": "monthly"},
            {"name": "Admission Fee", "amount": 6000, "frequency": "one_time"},
            {"name": "Exam Fee", "amount": 800, "frequency": "term"},
        ],
    },
    {
        "key": "higher_secondary",
        "name": "Higher secondary school",
        "desc": "Grades 11-12 with streams, electives and internal assessment.",
        "grades": GRADE_SETS["higher_secondary"],
        "modules": [m["key"] for m in MODULES],
        "fee_categories": [
            {"name": "Monthly Tuition", "amount": 6000, "frequency": "monthly"},
            {"name": "Lab Fee", "amount": 1500, "frequency": "term"},
        ],
    },
    {
        "key": "international",
        "name": "International school",
        "desc": "Cambridge-style stages, continuous assessment and multi-language support.",
        "grades": GRADE_SETS["international"],
        "modules": [m["key"] for m in MODULES],
        "fee_categories": [
            {"name": "Term Fee", "amount": 45000, "frequency": "term"},
            {"name": "Enrollment Fee", "amount": 25000, "frequency": "one_time"},
        ],
    },
    {
        "key": "private",
        "name": "Private school",
        "desc": "Flexible structure for schools that mix grades and sections.",
        "grades": GRADE_SETS["private"],
        "modules": [m["key"] for m in MODULES],
        "fee_categories": [
            {"name": "Monthly Tuition", "amount": 5000, "frequency": "monthly"},
            {"name": "Admission Fee", "amount": 10000, "frequency": "one_time"},
        ],
    },
    {
        "key": "public",
        "name": "Public school",
        "desc": "No-fee or subsidised structure with attendance and reporting focus.",
        "grades": GRADE_SETS["public"],
        "modules": [m["key"] for m in MODULES],
        "fee_categories": [
            {"name": "Exam Fee", "amount": 100, "frequency": "term"},
        ],
    },
    {
        "key": "small",
        "name": "Small school",
        "desc": "Compact workspace for small or tuition-style schools.",
        "grades": GRADE_SETS["small"],
        "modules": ["students", "classes", "attendance", "fees", "exams", "communication"],
        "fee_categories": [
            {"name": "Monthly Fee", "amount": 2000, "frequency": "monthly"},
        ],
    },
    {
        "key": "multi_campus",
        "name": "Multi-campus school",
        "desc": "Several campuses sharing one owner workspace with campus-labelled classes.",
        "grades": GRADE_SETS["multi_campus"],
        "modules": [m["key"] for m in MODULES],
        "fee_categories": [
            {"name": "Monthly Tuition", "amount": 3500, "frequency": "monthly"},
        ],
    },
    {
        "key": "custom",
        "name": "Custom school",
        "desc": "Start from an empty structure and build it with the School Builder.",
        "grades": [],
        "modules": [m["key"] for m in MODULES],
        "fee_categories": [],
    },
]


def list_templates() -> list[dict]:
    return TEMPLATES


def get_template(key: str) -> dict | None:
    for template in TEMPLATES:
        if template["key"] == key:
            return template
    return None
