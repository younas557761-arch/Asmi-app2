"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const authed = { credentials: "include" as const };

type dict = Record<string, unknown>;
type Plan = {
  id: string; command: string; status: string; engine: string;
  plan: { action: string | null; params: dict; confidence: string; validation: { ok: boolean; problems: string[] } };
};

const STATUS_BADGE: Record<string, string> = {
  pending: "badge",
  applied: "badge-green",
  rejected: "badge-red",
};

export default function BuilderPage() {
  const [command, setCommand] = useState("");
  const [plans, setPlans] = useState<Plan[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const res = await fetch(`${API}/api/v1/builder/plans`, authed);
    if (res.ok) setPlans((await res.json()).items);
  }, []);

  useEffect(() => { load(); }, [load]);

  async function plan() {
    setBusy(true);
    setError("");
    setNotice("");
    const res = await fetch(`${API}/api/v1/builder/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      ...authed,
      body: JSON.stringify({ command }),
    });
    setBusy(false);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { setError(data.detail || "Could not create plan"); return; }
    setNotice(data.status === "pending" ? "Plan ready — review it below and approve." : "Plan could not be validated (see problems).");
    setCommand("");
    load();
  }

  async function approve(planId: string) {
    setError("");
    setNotice("");
    const res = await fetch(`${API}/api/v1/builder/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      ...authed,
      body: JSON.stringify({ plan_id: planId }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { setError(data.detail || "Approval failed"); load(); return; }
    setNotice(`✅ ${data.result ?? "Plan applied."}`);
    load();
  }

  async function reject(planId: string) {
    setError("");
    const res = await fetch(`${API}/api/v1/builder/reject/${planId}`, { method: "POST", ...authed });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError(data.detail || "Reject failed");
    }
    load();
  }

  return (
    <div>
      <div className="page-head">
        <h1>School Builder</h1>
        <p>Describe a change in plain language. The builder drafts a typed plan — nothing happens until you approve it.</p>
      </div>
      {error && <p className="error">{error}</p>}
      {notice && <p className="muted">{notice}</p>}

      <div className="card">
        <div style={{ display: "flex", gap: "0.6rem" }}>
          <input
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && command.trim().length > 2 && plan()}
            placeholder='e.g. "Add a new Grade 6 class" or "create subject Physics"'
            style={{ flex: 1, marginBottom: 0 }}
          />
          <button type="button" onClick={plan} disabled={busy || command.trim().length < 3}>
            {busy ? "Planning…" : "Draft plan"}
          </button>
        </div>
        <p className="muted" style={{ marginTop: "0.6rem", marginBottom: 0 }}>
          Supported: add class · add subject · add fee category · academic year · enrol student · add teacher
        </p>
      </div>

      <div className="card">
        <h2>Plan history</h2>
        {plans.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">🏗️</div>
            <div className="empty-title">No plans yet</div>
            <div className="empty-hint">Type a command above to draft your first configuration plan.</div>
          </div>
        ) : (
          <table>
            <thead><tr><th>Command</th><th>Action</th><th>Validation</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {plans.map((p) => (
                <tr key={p.id}>
                  <td>{p.command}</td>
                  <td>{p.plan.action ?? "—"}</td>
                  <td>
                    {p.plan.validation?.ok
                      ? <span className="badge badge-green">valid</span>
                      : <span className="badge badge-red" title={p.plan.validation?.problems?.join("; ")}>{p.plan.validation?.problems?.[0] ?? "invalid"}</span>}
                  </td>
                  <td><span className={`badge ${STATUS_BADGE[p.status] ?? "badge-gray"}`}>{p.status}</span></td>
                  <td>
                    {p.status === "pending" && (
                      <>
                        <button type="button" className="qa-btn" onClick={() => approve(p.id)}>Approve</button>{" "}
                        <button type="button" className="qa-btn" onClick={() => reject(p.id)}>Reject</button>
                      </>
                    )}
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
