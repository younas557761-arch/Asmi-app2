import { headers } from "next/headers";
import { apiFetch } from "@/lib/api";
import AttendanceTrend from "./AttendanceTrend";

async function getJSON(path: string, cookie: string) {
  const res = await apiFetch(path, {}, cookie);
  if (!res.ok) return null;
  return res.json();
}

export default async function ReportsPage() {
  const cookie = (await headers()).get("cookie") || "";
  const [enrollment, fees] = await Promise.all([
    getJSON("/reports/enrollment", cookie),
    getJSON("/reports/fees", cookie),
  ]);

  return (
    <div>
      <div className="page-head">
        <h1>Reports</h1>
        <p>Enrollment, attendance trends and financial summary — from live database records</p>
      </div>

      <div className="grid">
        <div className="stat-card">
          <div className="stat-label">Total invoiced</div>
          <div className="stat-value">{fees?.invoiced ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Collected</div>
          <div className="stat-value">{fees?.collected ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Waived</div>
          <div className="stat-value">{fees?.waived ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Outstanding</div>
          <div className="stat-value">{fees?.outstanding ?? 0}</div>
        </div>
      </div>

      <div className="card">
        <h2>Enrollment by class</h2>
        {enrollment?.items?.length ? (
          <table>
            <thead><tr><th>Class</th><th>Students</th></tr></thead>
            <tbody>
              {enrollment.items.map((row: { class_name: string; students: number }) => (
                <tr key={row.class_name}>
                  <td>{row.class_name}</td>
                  <td>{row.students}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty"><div className="empty-title">No enrollment records</div></div>
        )}
      </div>

      <AttendanceTrend />
    </div>
  );
}
