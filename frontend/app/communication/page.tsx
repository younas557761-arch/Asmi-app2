"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const authed = { credentials: "include" as const };

type Announcement = {
  id: string; title: string; body: string; audience: string; class_name: string;
  status: string; published_at: string | null;
};

export default function CommunicationPage() {
  const [items, setItems] = useState<Announcement[]>([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    const res = await fetch(`${API}/api/v1/announcements${filter ? `?status=${filter}` : ""}`, authed);
    if (res.ok) setItems((await res.json()).items);
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  async function post(path: string, body?: unknown) {
    setError("");
    setNotice("");
    const res = await fetch(`${API}/api/v1${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      ...authed,
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { setError(data.detail || "Request failed"); return; }
    setNotice("Done.");
    load();
  }

  async function remove(id: string) {
    setError("");
    const res = await fetch(`${API}/api/v1/announcements/${id}`, { method: "DELETE", ...authed });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setError(data.detail || "Delete failed");
      return;
    }
    load();
  }

  return (
    <div>
      <div className="page-head">
        <h1>Communication</h1>
        <p>Announcements for everyone, parents only, or a single class. Drafts must be published before they are visible.</p>
      </div>
      {error && <p className="error">{error}</p>}
      {notice && <p className="muted">{notice}</p>}

      <div className="card">
        <h2>New announcement</h2>
        <form onSubmit={(e) => {
          e.preventDefault();
          const f = new FormData(e.currentTarget);
          post("/announcements", {
            title: f.get("title"),
            body: f.get("body"),
            audience: f.get("audience"),
            class_name: f.get("class_name") || "",
          }).then(() => e.currentTarget.reset());
        }}>
          <label>Title</label>
          <input name="title" placeholder="Parent-teacher meeting on Friday" required />
          <label>Message</label>
          <input name="body" placeholder="Details of the meeting…" required />
          <label>Audience</label>
          <select name="audience" defaultValue="all">
            <option value="all">Everyone</option>
            <option value="parents">Parents only</option>
            <option value="class">Single class</option>
          </select>
          <label>Class (required when audience is a class)</label>
          <input name="class_name" placeholder="Grade 1" />
          <button type="submit">Save draft</button>
        </form>
      </div>

      <div className="card">
        <div className="tabs">
          {["", "draft", "published"].map((f) => (
            <button key={f} type="button" className={`tab ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
              {f === "" ? "All" : f}
            </button>
          ))}
        </div>
        {items.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">📣</div>
            <div className="empty-title">No announcements yet</div>
            <div className="empty-hint">Publish notices for everyone, for parents only, or for a single class. Drafts must be published before they are visible.</div>
          </div>
        ) : (
          <table>
            <thead><tr><th>Title</th><th>Audience</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.id}>
                  <td>{a.title}</td>
                  <td>{a.audience === "class" ? `Class: ${a.class_name}` : a.audience}</td>
                  <td><span className={`badge ${a.status === "published" ? "badge-green" : "badge-gray"}`}>{a.status}</span></td>
                  <td>
                    {a.status === "draft" && (
                      <>
                        <button type="button" className="qa-btn" onClick={() => post(`/announcements/${a.id}/publish`)}>Publish</button>{" "}
                        <button type="button" className="qa-btn" onClick={() => remove(a.id)}>Delete</button>
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
