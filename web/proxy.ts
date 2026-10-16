import { auth } from "@/auth";

const oidcEnabled = Boolean(process.env.AUTH_OIDC_ISSUER);

// Next.js 16: proxy.ts replaces middleware.ts.
// When OIDC is not configured, this is a pass-through — the app runs
// in static-key mode and no login is required.
const middleware = auth((req) => {
  if (!oidcEnabled) return;
  if (!req.auth && req.nextUrl.pathname !== "/login") {
    const loginUrl = new URL("/login", req.nextUrl.origin);
    loginUrl.searchParams.set("callbackUrl", req.nextUrl.pathname);
    return Response.redirect(loginUrl);
  }
});

export default middleware;

export const config = {
  matcher: [
    "/((?!api/auth|api/proxy|_next/static|_next/image|favicon.ico|login|$).*)",
  ],
};
