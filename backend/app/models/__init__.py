from app.models.db import (  # noqa: F401
    AuditLog,
    EmailVerificationCode,
    PasswordResetToken,
    School,
    SchoolMembership,
    Session,
    Student,
    User,
)
from app.models.academic import (  # noqa: F401
    AcademicYear,
    AttendanceRecord,
    SchoolClass,
    Subject,
    Teacher,
)
from app.models.finance import (  # noqa: F401
    FeeCategory,
    FinancialAdjustment,
    Invoice,
    InvoiceItem,
    Payment,
)
from app.models.exams import (  # noqa: F401
    Examination,
    GradeBand,
    GradingScheme,
    Mark,
)
from app.models.people import (  # noqa: F401
    Announcement,
    Guardian,
    StudentGuardian,
)
from app.models.ai import (  # noqa: F401
    AIActionApproval,
    AIActionPlan,
)
