"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const authed = { credentials: "include" as const };

const STEPS = ["Template", "School details", "Modules", "Review"];
const TIMEZONES = ["Asia/Karachi", "Asia/Dubai", "Asia/Riyadh", "UTC", "Europe/London"];
const CURRENCIES = ["PKR", "USD", "EUR", "GBP", "AED", "SAR"];
const LANGUAGES = ["en", "ur", "ar", "hi", "fr", "es", "tr"];

type Template = { key: string; name: string; desc: string; grades: string[]; modules: string[] };
type Module = { key: string; name: string; desc: string };

export default function OnboardingWizard() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [modules, setModules] = useState<Module[]>([]);
  const [form, setForm] = useState({
    template_key: "primary",
    school_name: "",
    country: "Pakistan",
    city: "",
    timezone: "Asia/Karachi",
    currency: "PKR",
    language: "en",
    academic_year: "2026-2027",
  });
  const [enabled, setEnabled] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/api/v1/onboarding/templates`, authed).then((r) => r.json()).then((d) => setTemplates(d.items));
    fetch(`${API}/api/v1/onboarding/modules`, authed).then((r) => r.json()).then((d) => {
      setModules(d.items);
      setEnabled(d.items.map((m: Module) => m.key));
    });
  }, []);

  const template = templates.find((t) => t.key === form.template_key);

  function pickTemplate(key: string) {
    setForm((f) => ({ ...f, template_key: key }));
    const t = templates.find((x) => x.key === key);
    if (t) setEnabled(t.modules);
  }

  async function create() {
    setBusy(true);
    setError("");
    const res = await fetch(`${API}/api/v1/onboarding/create-workspace`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      ...authed,
      body: JSON.stringify({ ...form, modules: enabled }),
    });
    setBusy(false);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(data.detail || "Could not create workspace");
      return;
    }
    setReport(
      `Workspace ready: ${data.classes_created} classes, ${data.subjects_created} subjects, ` +
      `${data.fee_categories_created} fee categories created. Modules enabled: ${data.modules_enabled}.`
    );
    setTimeout(() => router.push("/dashboard"), 2500);
  }

  if (report) {
    return (
      <div className="card">
        <h2>✅ {report}</h2>
        <p className="muted">Opening your dashboard…</p>
      </div>
    );
  }

  return (
    <div>
      {/* Stepper */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
        {STEPS.map((label, i) => (
          <span key={label} className={`chip ${i === step ? "" : ""}`}
            style={i === step ? { borderColor: "var(--blue)", color: "var(--blue)", fontWeight: 600 } : {}}>
            {i + 1}. {label}
          </span>
        ))}
      </div>
      {error && <p className="error">{error}</p>}

      {/* Step 1: Template */}
      {step === 0 && (
        <div className="grid">
          {templates.map((t) => (
            <div key={t.key} className="card"
              onClick={() => pickTemplate(t.key)}
              style={{ cursor: "pointer", borderColor: form.template_key === t.key ? "var(--blue)" : undefined, borderWidth: form.template_key === t.key ? 2 : 1 }}>
              <h2>{t.name} {form.template_key === t.key && "✓"}</h2>
              <p className="muted">{t.desc}</p>
              <p className="muted">{t.grades.length} grade(s) · {t.modules.length} modules</p>
            </div>
          ))}
        </div>
      )}

      {/* Step 2: School details */}
      {step === 1 && (
        <div className="card" style={{ maxWidth: "560px" }}>
          <label>School name</label>
          <input value={form.school_name} onChange={(e) => setForm({ ...form, school_name: e.target.value })} placeholder="e.g. Al Noor Public School" />
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div style={{ flex: 1 }}>
              <label>Country</label>
              <input value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
            </div>
            <div style={{ flex: 1 }}>
              <label>City</label>
              <input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
            </div>
          </div>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div style={{ flex: 1 }}>
              <label>Time zone</label>
              <select value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })}>
                {TIMEZONES.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label>Currency</label>
              <select value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })}>
                {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div style={{ flex: 1 }}>
              <label>Interface language</label>
              <select value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })}>
                {LANGUAGES.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label>Academic year</label>
              <input value={form.academic_year} onChange={(e) => setForm({ ...form, academic_year: e.target.value })} />
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Modules */}
      {step === 2 && (
        <div className="grid">
          {modules.map((m) => (
            <label key={m.key} className="card" style={{ cursor: "pointer", margin: 0 }}>
              <div style={{ display: "flex", gap: "0.6rem", alignItems: "flex-start" }}>
                <input type="checkbox" style={{ width: "auto", marginTop: "0.2rem" }}
                  checked={enabled.includes(m.key)}
                  onChange={(e) =>
                    setEnabled((en) => (e.target.checked ? [...en, m.key] : en.filter((k) => k !== m.key)))
                  } />
                <span>
                  <strong>{m.name}</strong>
                  <div className="muted">{m.desc}</div>
                </span>
              </div>
            </label>
          ))}
        </div>
      )}

      {/* Step 4: Review */}
      {step === 3 && (
        <div className="card" style={{ maxWidth: "640px" }}>
          <h2>Review and create</h2>
          <table>
            <tbody>
              <tr><td className="muted">Template</td><td>{template?.name}</td></tr>
              <tr><td className="muted">School name</td><td>{form.school_name}</td></tr>
              <tr><td className="muted">Location</td><td>{form.city}, {form.country}</td></tr>
              <tr><td className="muted">Time zone</td><td>{form.timezone}</td></tr>
              <tr><td className="muted">Currency</td><td>{form.currency}</td></tr>
              <tr><td className="muted">Language</td><td>{form.language}</td></tr>
              <tr><td className="muted">Academic year</td><td>{form.academic_year}</td></tr>
              <tr><td className="muted">Modules</td><td>{enabled.length} selected</td></tr>
            </tbody>
          </table>
          <p className="muted">You can change any of this later in Settings and the School Builder.</p>
        </div>
      )}

      {/* Navigation */}
      <div style={{ display: "flex", gap: "0.6rem", marginTop: "1rem" }}>
        {step > 0 && <button type="button" className="qa-btn" onClick={() => setStep(step - 1)}>← Back</button>}
        {step < 3 && (
          <button type="button" onClick={() => (step === 1 && form.school_name.trim().length < 2 ? setError("Enter a school name") : (setError(""), setStep(step + 1)))}>
            Continue →
          </button>
        )}
        {step === 3 && (
          <button type="button" disabled={busy} onClick={create} style={{ background: "#16a34a" }}>
            {busy ? "Creating…" : "🎓 Create school workspace"}
          </button>
        )}
      </div>
    </div>
  );
}
