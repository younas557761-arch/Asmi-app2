"use client";

import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("asmi-theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = saved ? saved === "dark" : prefersDark;
    setDark(isDark);
    document.documentElement.dataset.theme = isDark ? "dark" : "light";
    setReady(true);
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
    localStorage.setItem("asmi-theme", next ? "dark" : "light");
  }

  if (!ready) return <button className="icon-btn" aria-label="Toggle theme" type="button">◐</button>;
  return (
    <button className="icon-btn" onClick={toggle} aria-label="Toggle theme" type="button">
      {dark ? "☀️" : "🌙"}
    </button>
  );
}
