import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const cookie = req.headers.get("cookie") || "";
  const upstream = await fetch(
    `${process.env.ASMI_API_URL || "http://localhost:8000"}/api/v1/auth/logout`,
    { method: "POST", headers: { Cookie: cookie } }
  );
  const res = NextResponse.json({ message: "Logged out" }, { status: upstream.status });
  res.headers.set("set-cookie", "asmi_session=; Path=/; HttpOnly; Max-Age=0; SameSite=Lax");
  return res;
}
