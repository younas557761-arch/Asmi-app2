"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Student = { id: string; admission_number: string; first_name: string; last_name: string };
type Balance = { student_id: string; admission_number: string; student_name: string; invoiced: number; paid: number; waived: number; balance: number };
type Invoice = { id: string; student_id: string; invoice_number: string; title: string; total: number; paid: number; waived: number; balance: number; status: string };

const STATUS_BADGE: Record<string, string> = {
  unpaid: "badge-red",
  partial: "badge-gray",
  paid: "badge-green",
};

export default function FeesPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const authed = { credentials: "include" as const };

  const load = useCallback(async () => {
    const [b, i, s] = await Promise.all([
      fetch(`${API}/api/v1/fees/balances`, authed),
      fetch(`${API}/api/v1/fees/invoices`, authed),
      fetch(`${API}/api/v1/students?size=200`, authed),
    ]);
    if (b.ok) setBalances((await b.json()).items);
    if (i.ok) setInvoices((await i.json()).items);
    if (s.ok) setStudents((await s.json()).items);
  }, []);

  useEffect(() => { load(); }, [load]);

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
    if (!res.ok) { setError(data.detail || "Request failed"); return; }
    setNotice("Saved.");
    load();
  }

  const studentOptions = students.map((s) => (
    <option key={s.id} value={s.id}>{s.admission_number} — {s.first_name} {s.last_name}</option>
  ));

  return (
    <div>
      <div className="page-head">
        <h1>Fees & Finance</h1>
        <p>Invoices, payments, waivers and outstanding balances</p>
      </div>
      {error && <p className="error">{error}</p>}
      {notice && <p className="muted">{notice}</p>}

      <div className="grid">
        <div className="card">
          <h2>Create invoice</h2>
          <form onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            post("/fees/invoices", {
              student_id: f.get("student_id"),
              title: f.get("title"),
              items: [{ description: f.get("description"), amount: Number(f.get("amount")) }],
              due_date: f.get("due_date") || null,
            });
            e.currentTarget.reset();
          }}>
            <label>Student</label>
            <select name="student_id" required>{studentOptions}</select>
            <label>Title</label>
            <input name="title" placeholder="October 2026 fee" required />
            <label>Item description</label>
            <input name="description" placeholder="Tuition" required />
            <label>Amount</label>
            <input name="amount" type="number" min="1" step="0.01" required />
            <label>Due date (optional)</label>
            <input name="due_date" type="date" />
            <button type="submit">Create invoice</button>
          </form>
        </div>

        <div className="card">
          <h2>Record payment</h2>
          <form onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            post("/fees/payments", {
              student_id: f.get("student_id"),
              invoice_id: f.get("invoice_id") || null,
              amount: Number(f.get("amount")),
              method: f.get("method"),
              note: f.get("note") || "",
            });
            e.currentTarget.reset();
          }}>
            <label>Student</label>
            <select name="student_id" required>{studentOptions}</select>
            <label>Invoice (optional)</label>
            <select name="invoice_id" defaultValue="">
              <option value="">— none (advance payment) —</option>
              {invoices.filter((i) => i.status !== "paid").map((i) => (
                <option key={i.id} value={i.id}>{i.invoice_number} · {i.title} · bal {i.balance}</option>
              ))}
            </select>
            <label>Amount</label>
            <input name="amount" type="number" min="1" step="0.01" required />
            <label>Method</label>
            <select name="method" defaultValue="cash">
              <option value="cash">Cash</option>
              <option value="bank">Bank</option>
              <option value="online">Online</option>
            </select>
            <label>Note</label>
            <input name="note" placeholder="Receipt reference" />
            <button type="submit">Record payment</button>
          </form>
        </div>

        <div className="card">
          <h2>Waiver / discount / refund</h2>
          <form onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            post("/fees/adjustments", {
              student_id: f.get("student_id"),
              invoice_id: f.get("invoice_id") || null,
              kind: f.get("kind"),
              amount: Number(f.get("amount")),
              reason: f.get("reason") || "",
            });
            e.currentTarget.reset();
          }}>
            <label>Student</label>
            <select name="student_id" required>{studentOptions}</select>
            <label>Invoice (optional)</label>
            <select name="invoice_id" defaultValue="">
              <option value="">— none —</option>
              {invoices.map((i) => (
                <option key={i.id} value={i.id}>{i.invoice_number} · {i.title}</option>
              ))}
            </select>
            <label>Kind</label>
            <select name="kind" defaultValue="waiver">
              <option value="waiver">Waiver</option>
              <option value="discount">Discount</option>
              <option value="refund">Refund</option>
            </select>
            <label>Amount</label>
            <input name="amount" type="number" min="1" step="0.01" required />
            <label>Reason</label>
            <input name="reason" placeholder="Staff child / merit / correction" required />
            <button type="submit">Save adjustment</button>
          </form>
        </div>
      </div>

      <div className="card">
        <h2>Outstanding balances</h2>
        {balances.length === 0 ? (
          <div className="empty"><div className="empty-title">No students yet</div></div>
        ) : (
          <table>
            <thead><tr><th>Adm #</th><th>Student</th><th>Invoiced</th><th>Paid</th><th>Waived</th><th>Balance</th></tr></thead>
            <tbody>
              {balances.map((b) => (
                <tr key={b.student_id}>
                  <td>{b.admission_number}</td>
                  <td>{b.student_name}</td>
                  <td>{b.invoiced}</td>
                  <td>{b.paid}</td>
                  <td>{b.waived}</td>
                  <td><strong>{b.balance}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h2>Invoices</h2>
        {invoices.length === 0 ? (
          <div className="empty"><div className="empty-title">No invoices yet</div></div>
        ) : (
          <table>
            <thead><tr><th>Number</th><th>Title</th><th>Total</th><th>Paid</th><th>Balance</th><th>Status</th></tr></thead>
            <tbody>
              {invoices.map((i) => (
                <tr key={i.id}>
                  <td>{i.invoice_number}</td>
                  <td>{i.title}</td>
                  <td>{i.total}</td>
                  <td>{i.paid}</td>
                  <td>{i.balance}</td>
                  <td><span className={`badge ${STATUS_BADGE[i.status] ?? ""}`}>{i.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
