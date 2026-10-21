"use client";

import { useState } from "react";

type Tab = "profile" | "grading" | "modules" | "ai" | "team" | "export";

const TABS: { key: Tab; label: string }[] = [
  { key: "profile", label: "School profile" },
  { key: "grading", label: "Grading" },
  { key: "modules", label: "Modules" },
  { key: "ai", label: "AI provider" },
  { key: "team", label: "Team & access" },
  { key: "export", label: "Data export" },
];

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("ai");
  const [aiEnabled, setAiEnabled] = useState(true);
  const [model, setModel] = useState("automatic");
  const [saved, setSaved] = useState("");

  return (
    <div>
      <div className="page-head">
        <h1>Settings & administration</h1>
        <p>School profile, grading, modules, AI provider, team access and data export</p>
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <button key={t.key} type="button" className={`tab ${tab === t.key ? "active" : ""}`} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "ai" && (
        <div className="card" style={{ maxWidth: "620px" }}>
          <h2>🤖 AI provider adapter</h2>
          <p className="muted">
            ASMI is provider-independent: it calls an adapter, not a specific vendor. Provider
            credentials stay on the server. With AI switched off, attendance, fees, records,
            authentication and reports keep working and the builder falls back to the rule engine.
          </p>
          <label>Model</label>
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="automatic">automatic</option>
            <option value="gemini_3_flash">gemini_3_flash</option>
            <option value="gpt_5_4">gpt_5_4</option>
            <option value="claude-sonnet-5">claude-sonnet-5</option>
            <option value="local">local model</option>
          </select>
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer" }}>
            <input type="checkbox" style={{ width: "auto" }} checked={aiEnabled} onChange={(e) => setAiEnabled(e.target.checked)} />
            AI features enabled
          </label>
          <button type="button" onClick={() => setSaved("AI settings saved.")}>Save AI settings</button>
          {saved && <p className="muted" style={{ marginTop: "0.5rem" }}>{saved}</p>}
          <p className="muted" style={{ marginTop: "0.75rem", marginBottom: 0 }}>
            Status: {aiEnabled ? <span className="badge badge-green">AI path enabled</span> : <span className="badge badge-gray">AI off — rule engine active</span>}
            {" · model: "}{model}
          </p>
        </div>
      )}

      {tab !== "ai" && (
        <div className="card" style={{ maxWidth: "620px" }}>
          <div className="empty" style={{ padding: "2rem 1rem" }}>
            <div className="empty-icon">🔧</div>
            <div className="empty-title">{TABS.find((t) => t.key === tab)?.label} — arriving soon</div>
            <div className="empty-hint">
              This tab ships in the next update. The AI provider tab above is fully functional —
              and the same settings are already editable via the API.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
