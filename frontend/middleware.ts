import { NextRequest, NextResponse } from "next/server";

const PROTECTED = [
  "/dashboard", "/students", "/teachers", "/parents", "/classes",
  "/attendance", "/timetable", "/exams", "/fees", "/reports",
  "/communication", "/assistant", "/builder", "/settings", "/security",
  "/onboarding", "/portal",
];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  // pass pathname to server components (used for active nav state)
  const reqHeaders = new Headers(req.headers);
  reqHeaders.set("x-pathname", pathname);
  const response = NextResponse.next({ request: { headers: reqHeaders } });
  if (PROTECTED.some((p) => pathname.startsWith(p))) {
    if (!req.cookies.get("asmi_session")) {
      const url = req.nextUrl.clone();
      url.pathname = "/login";
      return NextResponse.redirect(url);
    }
  }
  return response;
}

export const config = {
  matcher: PROTECTED.map((p) => `${p}/:path*`),
};
