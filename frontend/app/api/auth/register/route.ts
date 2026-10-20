import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const upstream = await fetch(
    `${process.env.ASMI_API_URL || "http://localhost:8000"}/api/v1/auth/register`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
  const res = NextResponse.json(await upstream.json().catch(() => ({})), {
    status: upstream.status,
  });
  const setCookie = upstream.headers.get("set-cookie");
  if (setCookie) res.headers.set("set-cookie", setCookie);
  return res;
}
