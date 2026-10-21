"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Day = { date: string; present: number; absent: number; late: number; excused: number; total: number };

export default function AttendanceTrend() {
  const today = new Date().toISOString().slice(0, 10);
  const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
  const [from, setFrom] = useState(monthAgo);
  const [to, setTo] = useState(today);
  const [days, setDays] = useState<Day[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    const res = await fetch(
      `${API}/api/v1/reports/attendance?from=${from}&to=${to}`,
      { credentials: "include" }
    );
    if (!res.ok) {
      setError("Could not load attendance report.");
      return;
    }
    setDays((await res.json()).items);
    setLoaded(true);
  }

  return (
    <div className="card">
      <h2>Attendance trend</h2>
      <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-end", flexWrap: "wrap" }}>
        <div>
          <label>From</label>
          <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} style={{ width: "auto" }} />
        </div>
        <div>
          <label>To</label>
          <input type="date" value={to} onChange={(e) => setTo(e.target.value)} style={{ width: "auto" }} />
        </div>
        <button type="button" className="qa-btn" onClick={load}>Load</button>
      </div>
      {error && <p className="error">{error}</p>}
      {loaded && days.length === 0 && <p className="muted">No attendance marked in this range.</p>}
      {days.length > 0 && (
        <table>
          <thead><tr><th>Date</th><th>Present</th><th>Absent</th><th>Late</th><th>Excused</th><th>Total</th></tr></thead>
          <tbody>
            {days.map((d) => (
              <tr key={d.date}>
                <td>{d.date}</td><td>{d.present}</td><td>{d.absent}</td><td>{d.late}</td><td>{d.excused}</td><td>{d.total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
