"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const STATUSES = ["present", "absent", "late", "excused"] as const;
type Status = (typeof STATUSES)[number];

type Student = { id: string; admission_number: string; first_name: string; last_name: string; class_name: string };
type Summary = { present: number; absent: number; late: number; excused: number; total: number; marked: boolean };

const LABELS: Record<Status, string> = { present: "P", absent: "A", late: "L", excused: "E" };

export default function AttendancePage() {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [className, setClassName] = useState("");
  const [students, setStudents] = useState<Student[]>([]);
  const [marks, setMarks] = useState<Record<string, Status>>({});
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const loadSummary = useCallback(async (d: string) => {
    const res = await fetch(`${API}/api/v1/attendance/summary?date=${d}`, { credentials: "include" });
    if (res.ok) setSummary(await res.json());
  }, []);

  const loadStudents = useCallback(async () => {
    setLoading(true);
    setError("");
    const res = await fetch(
      `${API}/api/v1/students?size=200${className ? `&class_name=${encodeURIComponent(className)}` : ""}`,
      { credentials: "include" }
    );
    setLoading(false);
    if (!res.ok) {
      setError("Could not load students. Are you signed in?");
      return;
    }
    const data = await res.json();
    setStudents(data.items);
    setMarks({});
  }, [className]);

  useEffect(() => {
    loadStudents();
    loadSummary(date);
  }, [loadStudents, loadSummary, date]);

  async function submit() {
    setError("");
    setNotice("");
    const records = Object.entries(marks).map(([student_id, status]) => ({ student_id, status }));
    if (records.length === 0) {
      setError("Mark at least one student before saving.");
      return;
    }
    setSubmitting(true);
    const res = await fetch(`${API}/api/v1/attendance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ date, records }),
    });
    setSubmitting(false);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(data.detail || "Could not save attendance");
      return;
    }
    setNotice(`Attendance saved for ${data.marked} student(s).`);
    setMarks({});
    loadSummary(date);
  }

  return (
    <div>
      <div className="page-head">
        <h1>Attendance</h1>
        <p>Daily register — present, absent, late, excused</p>
      </div>

      <div className="card">
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "flex-end" }}>
          <div>
            <label htmlFor="att-date">Date</label>
            <input id="att-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} style={{ width: "auto" }} />
          </div>
          <div>
            <label htmlFor="att-class">Class filter</label>
            <input id="att-class" value={className} onChange={(e) => setClassName(e.target.value)} placeholder="e.g. Grade 1" style={{ width: "180px" }} />
          </div>
          <div>
            <button type="button" onClick={loadStudents} disabled={loading} className="qa-btn">
              {loading ? "Loading…" : "Load register"}
            </button>
          </div>
          <div style={{ marginLeft: "auto" }}>
            <button type="button" onClick={submit} disabled={submitting}>
              {submitting ? "Saving…" : `Save attendance (${Object.keys(marks).length})`}
            </button>
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        {notice && <p className="muted">{notice}</p>}
      </div>

      {summary && (
        <div className="grid">
          <div className="stat-card"><div className="stat-label">Present</div><div className="stat-value">{summary.present}</div></div>
          <div className="stat-card"><div className="stat-label">Absent</div><div className="stat-value">{summary.absent}</div></div>
          <div className="stat-card"><div className="stat-label">Late</div><div className="stat-value">{summary.late}</div></div>
          <div className="stat-card"><div className="stat-label">Excused</div><div className="stat-value">{summary.excused}</div></div>
        </div>
      )}

      <div className="card">
        {students.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">✅</div>
            <div className="empty-title">No students to show</div>
            <div className="empty-hint">Add students first, then mark attendance here.</div>
          </div>
        ) : (
          <table>
            <thead>
              <tr><th>Admission #</th><th>Name</th><th>Class</th><th>Status</th></tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id}>
                  <td>{s.admission_number}</td>
                  <td>{s.first_name} {s.last_name}</td>
                  <td>{s.class_name || "—"}</td>
                  <td>
                    <div style={{ display: "flex", gap: "0.35rem" }}>
                      {STATUSES.map((st) => (
                        <button
                          key={st}
                          type="button"
                          onClick={() => setMarks((m) => ({ ...m, [s.id]: st }))}
                          style={{
                            padding: "0.3rem 0.6rem",
                            fontSize: "0.78rem",
                            background: marks[s.id] === st ? "var(--blue)" : "var(--surface)",
                            color: marks[s.id] === st ? "#fff" : "var(--text)",
                            border: "1px solid var(--border)",
                            borderRadius: "0.4rem",
                            cursor: "pointer",
                          }}
                          title={st}
                        >
                          {LABELS[st]}
                        </button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
