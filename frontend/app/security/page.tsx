"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const authed = { credentials: "include" as const };

type Entry = {
  id: string; action: string; detail: string; severity: string; source: string; created_at: string;
};

const SEV_CLASS: Record<string, string> = {
  info: "badge-gray",
  warning: "badge",
  critical: "badge-red",
};

export default function SecurityPage() {
  const [q, setQ] = useState("");
  const [severity, setSeverity] = useState("");
  const [source, setSource] = useState("");
  const [items, setItems] = useState<Entry[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (severity) params.set("severity", severity);
    if (source) params.set("source", source);
    const res = await fetch(`${API}/api/v1/audit-logs?${params}`, authed);
    if (!res.ok) {
      setError("Could not load audit logs. Are you signed in as the owner?");
      return;
    }
    const data = await res.json();
    setItems(data.items);
    setTotal(data.total);
  }, [q, severity, source]);

  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <div className="page-head">
        <h1>Security & Audit</h1>
        <p>Append-only trail of sensitive operations — {total} recorded action(s)</p>
      </div>
      {error && <p className="error">{error}</p>}

      <div className="card">
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "flex-end" }}>
          <div>
            <label>Search</label>
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search the summary…" style={{ width: "240px" }} />
          </div>
          <div>
            <label>Severity</label>
            <select value={severity} onChange={(e) => setSeverity(e.target.value)} style={{ width: "150px" }}>
              <option value="">All severities</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div>
            <label>Source</label>
            <select value={source} onChange={(e) => setSource(e.target.value)} style={{ width: "170px" }}>
              <option value="">All sources</option>
              <option value="user">User interface</option>
              <option value="ai_builder">AI builder</option>
              <option value="ai_assistant">AI assistant</option>
              <option value="system">System</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        {items.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">🛡️</div>
            <div className="empty-title">Nothing recorded yet</div>
            <div className="empty-hint">Sensitive actions like payments, waivers and result publishing will appear here automatically.</div>
          </div>
        ) : (
          <table>
            <thead><tr><th>When</th><th>Action</th><th>Detail</th><th>Severity</th><th>Source</th></tr></thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.id}>
                  <td style={{ whiteSpace: "nowrap" }}>{a.created_at.replace("T", " ").slice(0, 19)}</td>
                  <td>{a.action}</td>
                  <td className="muted">{a.detail || "—"}</td>
                  <td><span className={`badge ${SEV_CLASS[a.severity] ?? ""}`}>{a.severity}</span></td>
                  <td>{a.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
