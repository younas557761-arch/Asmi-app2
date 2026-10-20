import { headers } from "next/headers";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

async function getJSON(path: string, cookie: string) {
  const res = await apiFetch(path, {}, cookie);
  if (!res.ok) return null;
  return res.json();
}

export default async function DashboardPage() {
  const cookie = (await headers()).get("cookie") || "";
  const [me, summary] = await Promise.all([
    getJSON("/auth/me", cookie),
    getJSON("/dashboard/summary", cookie),
  ]);

  if (!me) {
    return (
      <div className="center-card">
        <h1>Session expired</h1>
        <Link className="btn" href="/login">Sign in again</Link>
      </div>
    );
  }

  const att = summary?.attendance_today;
  const checklist = summary?.setup_checklist ?? {};

  const stats = [
    {
      label: "Active students",
      value: summary?.students_active ?? "—",
      hint: "Enrolled records in your school",
    },
    {
      label: "Classes",
      value: summary?.classes_count ?? "—",
      hint: "Set up in Classes & Subjects",
    },
    {
      label: "Staff records",
      value: summary?.teachers_active ?? "—",
      hint: "Teachers & staff profiles",
    },
    {
      label: "Attendance today",
      value: att ? (att.marked ? `Marked (${att.present}P ${att.absent}A ${att.late}L ${att.excused}E)` : "Not marked") : "—",
      hint: summary?.date ?? "",
    },
  ];

  const steps = [
    { label: "Set up classes and sections", done: checklist.classes_created },
    { label: "Add or import students", done: checklist.students_added },
    { label: "Add your teaching staff", done: checklist.teachers_added },
    { label: "Take attendance today", done: checklist.attendance_marked_today },
  ];

  return (
    <div>
      <div className="page-head">
        <h1>{me.school.name}</h1>
        <p>
          {[me.school.city, me.school.country].filter(Boolean).join(", ")} · {me.school.timezone} · Role:{" "}
          <span className="badge">{me.role}</span>
        </p>
      </div>

      <div className="grid">
        {stats.map((s) => (
          <div className="stat-card" key={s.label}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value" style={{ fontSize: "1.15rem" }}>{s.value}</div>
            <div className="stat-hint">{s.hint}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h2>Quick actions</h2>
        <div className="quick-actions">
          <Link className="qa-btn" href="/students">🎓 Students</Link>
          <Link className="qa-btn" href="/classes">🏫 Classes & Subjects</Link>
          <Link className="qa-btn" href="/teachers">👩‍🏫 Teachers & Staff</Link>
          <Link className="qa-btn" href="/attendance">✅ Take attendance</Link>
          <span className="qa-btn" title="Arrives in Phase 3">💵 Record a payment <span className="soon-badge">soon</span></span>
          <span className="qa-btn" title="Arrives in Phase 3">📝 Enter exam marks <span className="soon-badge">soon</span></span>
        </div>
      </div>

      <div className="card">
        <h2>Workspace setup</h2>
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {steps.map((s) => (
            <li key={s.label} style={{ padding: "0.35rem 0" }}>
              {s.done ? "✅" : "⬜"} {s.label}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
