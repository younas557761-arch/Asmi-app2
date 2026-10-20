"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    const form = new FormData(e.currentTarget);
    if (form.get("password") !== form.get("confirm")) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        school_name: form.get("school_name"),
        email: form.get("email"),
        password: form.get("password"),
        full_name: form.get("full_name"),
        country: form.get("country"),
        city: form.get("city"),
        timezone: form.get("timezone") || "UTC",
        language: form.get("language") || "en",
        accept_terms: form.get("terms") === "on",
      }),
    });
    setLoading(false);
    if (res.ok) {
      router.push("/dashboard");
      router.refresh();
    } else {
      const data = await res.json().catch(() => ({}));
      setError(data.detail || "Registration failed");
    }
  }

  return (
    <div className="center-card">
      <h1>Create your school</h1>
      {error && <p className="error">{error}</p>}
      <form onSubmit={onSubmit}>
        <label htmlFor="school_name">School name</label>
        <input id="school_name" name="school_name" required />
        <label htmlFor="full_name">Your name</label>
        <input id="full_name" name="full_name" />
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" required />
        <label htmlFor="password">Password (min 8 chars)</label>
        <input id="password" name="password" type="password" minLength={8} required />
        <label htmlFor="confirm">Confirm password</label>
        <input id="confirm" name="confirm" type="password" minLength={8} required />
        <label htmlFor="country">Country</label>
        <input id="country" name="country" />
        <label htmlFor="city">City</label>
        <input id="city" name="city" />
        <label htmlFor="timezone">Time zone</label>
        <input id="timezone" name="timezone" defaultValue="UTC" />
        <label htmlFor="language">Language</label>
        <input id="language" name="language" defaultValue="en" />
        <label>
          <input type="checkbox" name="terms" style={{ width: "auto", marginRight: "0.5rem" }} />
          I accept the terms and privacy notice
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Creating…" : "Create school"}
        </button>
      </form>
    </div>
  );
}
