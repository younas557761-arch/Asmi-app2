"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Year = { id: string; name: string; is_current: boolean };
type SchoolClass = { id: string; name: string; capacity: number; academic_year_id: string };
type Subject = { id: string; name: string; code: string };

export default function ClassesManager({
  years,
  classes,
  subjects,
}: {
  years: Year[];
  classes: SchoolClass[];
  subjects: Subject[];
}) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  async function post(path: string, body: unknown) {
    setError("");
    setInfo("");
    const res = await fetch(`${API}/api/v1${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(data.detail || "Request failed");
      return false;
    }
    setInfo("Saved.");
    router.refresh();
    return true;
  }

  async function remove(path: string) {
    setError("");
    const res = await fetch(`${API}/api/v1${path}`, {
      method: "DELETE",
      credentials: "include",
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError(data.detail || "Delete failed");
      return;
    }
    router.refresh();
  }

  return (
    <div>
      {error && <p className="error">{error}</p>}
      {info && <p className="muted">{info}</p>}

      <div className="grid">
        <div className="card">
          <h2>Academic year</h2>
          <form onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            post("/academic-years", {
              name: f.get("name"),
              start_date: f.get("start_date"),
              end_date: f.get("end_date"),
            });
            e.currentTarget.reset();
          }}>
            <label>Year name</label>
            <input name="name" placeholder="2026-2027" required />
            <label>Starts</label>
            <input name="start_date" type="date" required />
            <label>Ends</label>
            <input name="end_date" type="date" required />
            <button type="submit">Add year</button>
          </form>
          {years.length > 0 && (
            <table>
              <thead><tr><th>Year</th><th>Status</th><th /></tr></thead>
              <tbody>
                {years.map((y) => (
                  <tr key={y.id}>
                    <td>{y.name}</td>
                    <td>{y.is_current ? <span className="badge">current</span> : <span className="badge badge-gray">—</span>}</td>
                    <td>{!y.is_current && <button type="button" className="qa-btn" onClick={() => post(`/academic-years/${y.id}/activate`, {})}>Set current</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <h2>Classes</h2>
          <form onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            post("/classes", { name: f.get("name"), capacity: Number(f.get("capacity") || 40) });
            e.currentTarget.reset();
          }}>
            <label>Class name</label>
            <input name="name" placeholder="Grade 1" required />
            <label>Capacity</label>
            <input name="capacity" type="number" defaultValue={40} min={1} max={500} />
            <button type="submit">Add class</button>
          </form>
          {classes.length > 0 && (
            <table>
              <thead><tr><th>Class</th><th>Capacity</th><th /></tr></thead>
              <tbody>
                {classes.map((c) => (
                  <tr key={c.id}>
                    <td>{c.name}</td>
                    <td>{c.capacity}</td>
                    <td><button type="button" className="qa-btn" onClick={() => remove(`/classes/${c.id}`)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <h2>Subjects</h2>
          <form onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            post("/subjects", { name: f.get("name"), code: f.get("code") || "" });
            e.currentTarget.reset();
          }}>
            <label>Subject name</label>
            <input name="name" placeholder="Mathematics" required />
            <label>Code (optional)</label>
            <input name="code" placeholder="MATH" />
            <button type="submit">Add subject</button>
          </form>
          {subjects.length > 0 && (
            <table>
              <thead><tr><th>Subject</th><th>Code</th><th /></tr></thead>
              <tbody>
                {subjects.map((s) => (
                  <tr key={s.id}>
                    <td>{s.name}</td>
                    <td>{s.code || "—"}</td>
                    <td><button type="button" className="qa-btn" onClick={() => remove(`/subjects/${s.id}`)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
