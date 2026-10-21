import "./globals.css";
import Link from "next/link";
import { headers } from "next/headers";
import { apiFetch } from "@/lib/api";
import ThemeToggle from "./components/ThemeToggle";
import type { ReactNode } from "react";

export const metadata = {
  title: "ASMI — Artificial School Management Intelligent",
  description: "Global AI school software builder",
};

type NavItem = { href?: string; label: string; soon?: boolean };

const NAV: { section: string | null; items: NavItem[] }[] = [
  { section: null, items: [
    { href: "/dashboard", label: "Home" },
    { href: "/builder", label: "School Builder" },
  ]},
  { section: null, items: [
    { href: "/students", label: "Students" },
    { href: "/teachers", label: "Teachers & Staff" },
    { label: "Parents", soon: true },
    { href: "/classes", label: "Classes & Subjects" },
    { href: "/attendance", label: "Attendance" },
    { label: "Timetable", soon: true },
    { href: "/exams", label: "Examinations" },
    { href: "/fees", label: "Fees & Finance" },
    { href: "/reports", label: "Reports" },
    { href: "/communication", label: "Communication" },
    { href: "/assistant", label: "AI Assistant" },
  ]},
  { section: "Administration", items: [
    { href: "/settings", label: "Settings" },
    { href: "/security", label: "Security & Audit" },
  ]},
];

function NavLinks({ pathname }: { pathname: string }) {
  return NAV.map((group, i) => (
    <div key={i}>
      {group.section && <div className="nav-section">{group.section}</div>}
      {group.items.map((item) =>
        item.href && !item.soon ? (
          <Link
            key={item.label}
            href={item.href}
            className={`nav-link ${pathname.startsWith(item.href) ? "active" : ""}`}
          >
            {item.label}
          </Link>
        ) : (
          <span key={item.label} className="nav-soon">
            {item.label}
            <span className="soon-badge">soon</span>
          </span>
        )
      )}
    </div>
  ));
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const h = await headers();
  const cookie = h.get("cookie") || "";
  const pathname = h.get("x-pathname") || "";

  let me: any = null;
  if (cookie.includes("asmi_session")) {
    const res = await apiFetch("/auth/me", {}, cookie);
    if (res.ok) me = await res.json();
  }

  if (!me) {
    return (
      <html lang="en">
        <body>
          <div className="auth-wrap">
            <div className="auth-brand">
              <span className="school-logo">🎓</span>
              <div>
                <div className="school-name">ASMI</div>
                <div className="school-sub">Artificial School Management Intelligent</div>
              </div>
            </div>
            <main className="auth-main">{children}</main>
          </div>
        </body>
      </html>
    );
  }

  const initials = (me.full_name || me.email || "?").slice(0, 1).toUpperCase();
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <aside className="sidebar">
            <div className="school-block">
              <span className="school-logo">🎓</span>
              <div>
                <div className="school-name">{me.school.name}</div>
                <div className="school-sub">
                  {[me.school.city, me.school.country].filter(Boolean).join(", ")}
                </div>
              </div>
            </div>
            <nav className="nav">
              <NavLinks pathname={pathname} />
            </nav>
            <div className="user-card">
              <span className="avatar">{initials}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="user-name">{me.full_name || me.email}</div>
                <div className="user-role">{me.role}</div>
              </div>
              <form action="/api/auth/logout" method="post">
                <button className="logout-btn" type="submit">Sign out</button>
              </form>
            </div>
          </aside>
          <div className="main-col">
            <header className="topbar">
              <div className="topbar-group">
                <span className="chip">🕐 {me.school.timezone}</span>
                <span className="chip">🌐 {me.school.language}</span>
              </div>
              <div className="topbar-group">
                <Link href="/assistant" className="chip" title="Open the AI Assistant">✨ AI Assistant</Link>
                <ThemeToggle />
              </div>
            </header>
            <main className="content">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
