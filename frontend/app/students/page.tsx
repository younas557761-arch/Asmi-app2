import { headers } from "next/headers";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

type Student = {
  id: string;
  admission_number: string;
  first_name: string;
  last_name: string;
  class_name: string;
  section: string;
  status: string;
};

export default async function StudentsPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const cookie = (await headers()).get("cookie") || "";
  const { q = "" } = await searchParams;
  const res = await apiFetch(
    `/students?size=50${q ? `&q=${encodeURIComponent(q)}` : ""}`,
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
  const data: { items: Student[]; total: number } = await res.json();

  return (
    <div>
      <div className="page-head">
        <h1>Students</h1>
        <p>{data.total} record(s)</p>
      </div>
      <form method="get" style={{ marginBottom: "1rem" }}>
        <input
          type="search"
          name="q"
          placeholder="Search name or admission number…"
          defaultValue={q}
          style={{ maxWidth: "340px" }}
        />
      </form>
      <div className="card">
        {data.items.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">🎓</div>
            <div className="empty-title">No students yet</div>
            <div className="empty-hint">
              Enrol your first student through the API (POST /api/v1/students)
              or the admission form arriving in Phase 2.
            </div>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Admission #</th><th>Name</th><th>Class</th><th>Section</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((s) => (
                <tr key={s.id}>
                  <td>{s.admission_number}</td>
                  <td>{s.first_name} {s.last_name}</td>
                  <td>{s.class_name}</td>
                  <td>{s.section}</td>
                  <td><span className="badge">{s.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
