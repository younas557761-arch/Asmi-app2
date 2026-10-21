"use client";

import { useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const authed = { credentials: "include" as const };

type Message = { role: "user" | "assistant"; text: string; figures?: Record<string, unknown> };
type Suggestion = string;

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API}/api/v1/assistant/suggestions`, authed)
      .then((r) => r.json())
      .then((d) => setSuggestions(d.items));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function ask(question: string) {
    if (!question.trim() || busy) return;
    setBusy(true);
    setError("");
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    const res = await fetch(`${API}/api/v1/assistant/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      ...authed,
      body: JSON.stringify({ question }),
    });
    setBusy(false);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(data.detail || "The assistant could not answer.");
      return;
    }
    setMessages((m) => [...m, { role: "assistant", text: data.text, figures: data.figures }]);
  }

  return (
    <div>
      <div className="page-head">
        <h1>AI Assistant</h1>
        <p>Answers from your live school data — attendance, fees, enrollment, workflows</p>
      </div>
      {error && <p className="error">{error}</p>}

      <div className="grid" style={{ gridTemplateColumns: "2fr 1fr" }}>
        <div className="card" style={{ minHeight: "420px", display: "flex", flexDirection: "column" }}>
          <div style={{ flex: 1, overflowY: "auto", marginBottom: "0.75rem" }}>
            {messages.length === 0 && (
              <div className="empty" style={{ padding: "2rem 1rem" }}>
                <div className="empty-icon">✨</div>
                <div className="empty-title">Ask about your school</div>
                <div className="empty-hint">Try a suggestion on the right, or type your own question.</div>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} style={{
                marginBottom: "0.6rem",
                padding: "0.6rem 0.85rem",
                borderRadius: "0.6rem",
                background: msg.role === "user" ? "var(--blue)" : "var(--bg)",
                color: msg.role === "user" ? "#fff" : "var(--text)",
                marginLeft: msg.role === "user" ? "15%" : "0",
                marginRight: msg.role === "user" ? "0" : "15%",
                whiteSpace: "pre-wrap",
              }}>
                {msg.text}
              </div>
            ))}
            {busy && <p className="muted">Thinking…</p>}
            <div ref={bottomRef} />
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && ask(input)}
              placeholder="Ask about enrolment, attendance, fees, results…"
              style={{ flex: 1, marginBottom: 0 }}
            />
            <button type="button" onClick={() => ask(input)} disabled={busy}>Ask</button>
          </div>
        </div>

        <div>
          <div className="card">
            <h2>Suggestions</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {suggestions.map((s) => (
                <button key={s} type="button" className="qa-btn" style={{ justifyContent: "flex-start" }}
                  onClick={() => ask(s)} disabled={busy}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="card">
            <h2>Live figures used</h2>
            {(() => {
              const last = [...messages].reverse().find((m) => m.role === "assistant" && m.figures && Object.keys(m.figures).length > 0);
              if (!last) return <p className="muted">Ask a question and the figures the assistant used will appear here.</p>;
              return (
                <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.78rem", margin: 0 }}>
                  {JSON.stringify(last.figures, null, 2)}
                </pre>
              );
            })()}
          </div>

          <div className="card">
            <h2>AI provider</h2>
            <p className="muted" style={{ margin: 0 }}>
              <span className="badge">rule engine</span>
              <br /><br />
              Working without an external AI provider. Core school operations are unaffected.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
