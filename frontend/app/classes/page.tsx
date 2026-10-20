import { headers } from "next/headers";
import { apiFetch } from "@/lib/api";
import ClassesManager from "./ClassesManager";

async function getJSON(path: string, cookie: string) {
  const res = await apiFetch(path, {}, cookie);
  if (!res.ok) return null;
  return res.json();
}

export default async function ClassesPage() {
  const cookie = (await headers()).get("cookie") || "";
  const [years, classes, subjects] = await Promise.all([
    getJSON("/academic-years", cookie),
    getJSON("/classes", cookie),
    getJSON("/subjects", cookie),
  ]);

  return (
    <div>
      <div className="page-head">
        <h1>Classes & Subjects</h1>
        <p>Academic years, classes and the subjects you teach</p>
      </div>
      <ClassesManager
        years={years?.items ?? []}
        classes={classes?.items ?? []}
        subjects={subjects?.items ?? []}
      />
    </div>
  );
}
