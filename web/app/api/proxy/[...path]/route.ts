import { NextRequest } from "next/server";
import { auth } from "@/auth";

const BACKEND = process.env.STORESIGNAL_API_BASE ?? "http://localhost:8790";
const API_KEY = process.env.STORESIGNAL_API_KEY ?? "demo-key-storesignal";

async function forward(req: NextRequest, params: Promise<{ path: string[] }>) {
  const { path } = await params;
  const target = `${BACKEND}/${path.join("/")}${req.nextUrl.search}`;

  const headers = new Headers();
  req.headers.forEach((v, k) => {
    const lk = k.toLowerCase();
    if (lk === "host") return;
    if (lk === "authorization") return; // strip browser-supplied auth
    headers.set(k, v);
  });

  // Prefer the OIDC access token from the Auth.js session (server-side).
  // Fall back to the static x-api-key when OIDC is not configured.
  try {
    const session = await auth();
    if (session?.accessToken) {
      headers.set("authorization", `Bearer ${session.accessToken}`);
    } else {
      headers.set("x-api-key", API_KEY);
    }
  } catch {
    headers.set("x-api-key", API_KEY);
  }

  const body =
    req.method === "GET" || req.method === "HEAD" ? undefined : await req.text();

  const res = await fetch(target, {
    method: req.method,
    headers,
    body,
    cache: "no-store",
  });

  const out = new Headers();
  res.headers.forEach((v, k) => {
    if (k.toLowerCase() === "content-encoding") return;
    out.set(k, v);
  });
  out.set("cache-control", "no-store");

  return new Response(res.body, { status: res.status, headers: out });
}

export const GET = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  forward(req, ctx.params);
export const POST = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  forward(req, ctx.params);
export const PATCH = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  forward(req, ctx.params);
export const PUT = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  forward(req, ctx.params);
export const DELETE = (req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) =>
  forward(req, ctx.params);
