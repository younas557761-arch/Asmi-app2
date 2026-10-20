import { headers } from "next/headers";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

type Teacher = {
  id: string;
  employee_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  subject: string;
  status: string;
};

export default async function TeachersPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const cookie = (await headers()).get("cookie") || "";
  const { q = "" } = await searchParams;
  const res = await apiFetch(
    `/teachers?size=50${q ? `&q=${encodeURIComponent(q)}` : ""}`,
    {},
    cookie
  );
  if (!res.ok) {
    return (
      <div className="center-card">
        <h1>Please sign in</h1>
        <Link className="btn" href="/login">Sign in</Link>
      </div>
    );
  }
  const data: { items: Teacher[]; total: number } = await res.json();

  return (
    <div>
      <div className="page-head">
        <h1>Teachers & Staff</h1>
        <p>{data.total} record(s)</p>
      </div>
      <form method="get" style={{ marginBottom: "1rem" }}>
        <input
          type="search"
          name="q"
          placeholder="Search name or employee number…"
          defaultValue={q}
          style={{ maxWidth: "340px" }}
        />
      </form>
      <div className="card">
        {data.items.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">👩‍🏫</div>
            <div className="empty-title">No staff records yet</div>
            <div className="empty-hint">
              Add your teaching staff through the API (POST /api/v1/teachers).
              The staff form arrives with the management UI in a later update.
            </div>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Emp #</th><th>Name</th><th>Subject</th><th>Email</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((t) => (
                <tr key={t.id}>
                  <td>{t.employee_number}</td>
                  <td>{t.first_name} {t.last_name}</td>
                  <td>{t.subject || "—"}</td>
                  <td>{t.email || "—"}</td>
                  <td><span className="badge">{t.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
