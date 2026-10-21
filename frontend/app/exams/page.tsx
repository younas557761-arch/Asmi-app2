"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const authed = { credentials: "include" as const };

type Student = { id: string; admission_number: string; first_name: string; last_name: string };
type Exam = { id: string; name: string; start_date: string; end_date: string; published: boolean };
type Result = {
  student_id: string; admission_number: string; student_name: string;
  total_obtained: number; total_max: number; percentage: number; grade: string; passed: boolean;
};

export default function ExamsPage() {
  const [exams, setExams] = useState<Exam[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedExam, setSelectedExam] = useState("");
  const [results, setResults] = useState<Result[]>([]);
  const [published, setPublished] = useState(false);
  const [bands, setBands] = useState([
    { grade: "A", min_percentage: 80 },
    { grade: "B", min_percentage: 60 },
    { grade: "F", min_percentage: 0 },
  ]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    const [e, s] = await Promise.all([
      fetch(`${API}/api/v1/exams`, authed),
      fetch(`${API}/api/v1/students?size=200`, authed),
    ]);
    if (e.ok) setExams((await e.json()).items);
    if (s.ok) setStudents((await s.json()).items);
  }, []);

  const loadResults = useCallback(async (examId: string) => {
    const res = await fetch(`${API}/api/v1/exams/${examId}/results`, authed);
    if (res.ok) {
      const data = await res.json();
      setResults(data.items);
      setPublished(data.published);
    }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { if (selectedExam) loadResults(selectedExam); }, [selectedExam, loadResults]);

  async function post(path: string, body: unknown) {
    setError("");
    setNotice("");
    const res = await fetch(`${API}/api/v1${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      ...authed,
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { setError(data.detail || "Request failed"); return null; }
    setNotice("Saved.");
    return data;
  }

  const studentOptions = students.map((s) => (
    <option key={s.id} value={s.id}>{s.admission_number} — {s.first_name} {s.last_name}</option>
  ));

  const selected = exams.find((e) => e.id === selectedExam);

  return (
    <div>
      <div className="page-head">
        <h1>Examinations</h1>
        <p>Grading schemes, marks entry and result publication</p>
      </div>
      {error && <p className="error">{error}</p>}
      {notice && <p className="muted">{notice}</p>}

      <div className="grid">
        <div className="card">
          <h2>Grading scheme</h2>
          <form onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            post("/exams/schemes", {
              name: f.get("name"),
              pass_mark: Number(f.get("pass_mark")),
              bands: bands.filter((b) => b.grade),
            });
          }}>
            <label>Scheme name</label>
            <input name="name" placeholder="Standard A-F" required />
            <label>Pass mark (%)</label>
            <input name="pass_mark" type="number" defaultValue={40} min={0} max={100} />
            {bands.map((band, idx) => (
              <div key={idx} style={{ display: "flex", gap: "0.5rem" }}>
                <input value={band.grade} placeholder="Grade"
                  onChange={(e) => setBands((bs) => bs.map((b, i) => i === idx ? { ...b, grade: e.target.value } : b))} style={{ width: "80px" }} />
                <input value={band.min_percentage} placeholder="Min %" type="number"
                  onChange={(e) => setBands((bs) => bs.map((b, i) => i === idx ? { ...b, min_percentage: Number(e.target.value) } : b))} style={{ width: "100px" }} />
                <button type="button" className="qa-btn" onClick={() => setBands((bs) => bs.filter((_, i) => i !== idx))}>✕</button>
              </div>
            ))}
            <button type="button" className="qa-btn" onClick={() => setBands((bs) => [...bs, { grade: "", min_percentage: 0 }])}>+ Add band</button>
            <div style={{ marginTop: "0.75rem" }}><button type="submit">Save scheme</button></div>
          </form>
        </div>

        <div className="card">
          <h2>Create examination</h2>
          <form onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            post("/exams", {
              name: f.get("name"),
              start_date: f.get("start_date"),
              end_date: f.get("end_date"),
            }).then(() => load());
            e.currentTarget.reset();
          }}>
            <label>Name</label>
            <input name="name" placeholder="Midterm 2026" required />
            <label>Starts</label>
            <input name="start_date" type="date" required />
            <label>Ends</label>
            <input name="end_date" type="date" required />
            <button type="submit">Create examination</button>
          </form>
          {exams.length > 0 && (
            <table>
              <thead><tr><th>Exam</th><th>Status</th><th /></tr></thead>
              <tbody>
                {exams.map((e) => (
                  <tr key={e.id}>
                    <td>{e.name}</td>
                    <td>{e.published ? <span className="badge badge-green">published</span> : <span className="badge badge-gray">draft</span>}</td>
                    <td><button type="button" className="qa-btn" onClick={() => setSelectedExam(e.id)}>Open</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {selected && (
          <div className="card">
            <h2>Enter marks — {selected.name}</h2>
            {published ? (
              <p className="muted">Results are published. Marks are locked.</p>
            ) : (
              <form onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                post(`/exams/${selected.id}/marks`, {
                  records: [{
                    student_id: f.get("student_id"),
                    subject: f.get("subject"),
                    max_marks: Number(f.get("max_marks")),
                    marks_obtained: Number(f.get("marks_obtained")),
                  }],
                }).then(() => loadResults(selected.id));
                e.currentTarget.reset();
              }}>
                <label>Student</label>
                <select name="student_id" required>{studentOptions}</select>
                <label>Subject</label>
                <input name="subject" placeholder="Mathematics" required />
                <label>Max marks</label>
                <input name="max_marks" type="number" defaultValue={100} min={1} required />
                <label>Marks obtained</label>
                <input name="marks_obtained" type="number" defaultValue={0} min={0} required />
                <button type="submit">Save marks</button>
              </form>
            )}
            {!published && results.length > 0 && (
              <button
                type="button"
                style={{ marginTop: "0.75rem", background: "#16a34a" }}
                onClick={() => post(`/exams/${selected.id}/publish`, {}).then(() => loadResults(selected.id))}
              >
                Publish results
              </button>
            )}
          </div>
        )}
      </div>

      {selected && results.length > 0 && (
        <div className="card">
          <h2>Results — {selected.name} {published ? "(published)" : "(preview)"}</h2>
          <table>
            <thead><tr><th>Adm #</th><th>Student</th><th>Total</th><th>%</th><th>Grade</th><th>Result</th></tr></thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.student_id}>
                  <td>{r.admission_number}</td>
                  <td>{r.student_name}</td>
                  <td>{r.total_obtained} / {r.total_max}</td>
                  <td>{r.percentage}</td>
                  <td><span className="badge">{r.grade || "—"}</span></td>
                  <td>{r.passed ? <span className="badge badge-green">pass</span> : <span className="badge badge-red">fail</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
