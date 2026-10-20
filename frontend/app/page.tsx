import Link from "next/link";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

export default async function Home() {
  const cookie = (await headers()).get("cookie") || "";
  if (cookie.includes("asmi_session")) redirect("/dashboard");

  return (
    <div className="center-card">
      <h1>ASMI</h1>
      <p className="muted">
        Artificial School Management Intelligent — build and run your school&apos;s
        software on your own infrastructure.
      </p>
      <div style={{ display: "flex", gap: "0.6rem", marginTop: "1rem" }}>
        <Link className="btn" href="/register">Create your school</Link>
        <Link className="btn" href="/login" style={{ background: "var(--slate)" }}>Sign in</Link>
      </div>
    </div>
  );
}
