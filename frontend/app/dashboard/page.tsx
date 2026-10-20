import { headers } from "next/headers";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

async function getMe(cookie: string) {
  const res = await apiFetch("/auth/me", {}, cookie);
  if (!res.ok) return null;
  return res.json();
}

async function getStudents(cookie: string) {
  const res = await apiFetch("/students?size=1", {}, cookie);
  if (!res.ok) return { total: 0 };
  return res.json();
}

export default async function DashboardPage() {
  const cookie = (await headers()).get("cookie") || "";
  const [me, students] = await Promise.all([getMe(cookie), getStudents(cookie)]);

  if (!me) {
    return (
      <div className="center-card">
        <h1>Session expired</h1>
        <Link className="btn" href="/login">Sign in again</Link>
      </div>
    );
  }

  // Real data only: students count is live; attendance/fees modules arrive in P2/P3
  const stats = [
    { label: "Active students", value: students.total, hint: "Enrolled records in your school" },
    { label: "Attendance today", value: "—", hint: "Attendance module arrives in Phase 2" },
    { label: "Staff records", value: "—", hint: "Teachers module arrives in Phase 2" },
    { label: "Fees outstanding", value: "—", hint: "Fees module arrives in Phase 3" },
  ];

  return (
    <div>
      <div className="page-head">
        <h1>{me.school.name}</h1>
        <p>{[me.school.city, me.school.country].filter(Boolean).join(", ")} · {me.school.timezone} · Role: <span className="badge">{me.role}</span></p>
      </div>

      <div className="grid">
        {stats.map((s) => (
          <div className="stat-card" key={s.label}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value">{s.value}</div>
            <div className="stat-hint">{s.hint}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h2>Quick actions</h2>
        <div className="quick-actions">
          <Link className="qa-btn" href="/students">🎓 Enrol a student</Link>
          <span className="qa-btn" title="Arrives in Phase 2">✅ Take attendance <span className="soon-badge">soon</span></span>
          <span className="qa-btn" title="Arrives in Phase 3">💵 Record a payment <span className="soon-badge">soon</span></span>
          <span className="qa-btn" title="Arrives in Phase 3">📝 Enter exam marks <span className="soon-badge">soon</span></span>
          <span className="qa-btn" title="Arrives in Phase 3">👨‍👩‍👧 Invite parents <span className="soon-badge">soon</span></span>
        </div>
      </div>

      <div className="card">
        <h2>Workspace setup</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          ✅ Foundation live: registration, login, tenant isolation, student records.
          Next: classes, attendance, staff — then fees, exams, AI builder.
          Full checklist in docs/STATUS.md.
        </p>
      </div>
    </div>
  );
}
