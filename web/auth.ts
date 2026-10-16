import NextAuth from "next-auth";

// Provider-agnostic OIDC. Set these env vars in web/.env.local:
//   AUTH_OIDC_ISSUER       e.g. http://localhost:8080/realms/storesignal
//   AUTH_OIDC_CLIENT_ID    e.g. storesignal-api
//   AUTH_OIDC_CLIENT_SECRET (leave empty for public/PKCE clients)
//   AUTH_OIDC_ROLE_CLAIM   e.g. realm_access.roles  (default: "roles")
//   AUTH_SECRET            random 32-byte base64 (openssl rand -base64 32)
//
// When AUTH_OIDC_ISSUER is unset, OIDC is disabled and the app falls back
// to the static x-api-key path (demo mode) — no login required.

const oidcEnabled = Boolean(process.env.AUTH_OIDC_ISSUER);
const roleClaim = process.env.AUTH_OIDC_ROLE_CLAIM || "roles";

export const { handlers, auth, signIn, signOut } = NextAuth({
  secret: process.env.AUTH_SECRET,
  trustHost: true,
  providers: oidcEnabled
    ? [
        {
          id: "storesignal-oidc",
          name: "StoreSignal SSO",
          type: "oidc",
          issuer: process.env.AUTH_OIDC_ISSUER,
          clientId: process.env.AUTH_OIDC_CLIENT_ID,
          clientSecret: process.env.AUTH_OIDC_CLIENT_SECRET || undefined,
          authorization: { params: { scope: "openid profile email" } },
        },
      ]
    : [],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.expiresAt = account.expires_at;
        token.provider = account.provider;
      }
      if (profile) {
        // Extract role from the configured claim. Keycloak nests it under
        // realm_access.roles; Auth0 uses a namespaced claim. Support both.
        const claims = profile as Record<string, unknown>;
        let raw: unknown = claims[roleClaim];
        if (raw === undefined && roleClaim.includes(".")) {
          // walk dotted path: realm_access.roles
          raw = roleClaim.split(".").reduce<unknown>((acc, key) => {
            if (acc && typeof acc === "object" && key in (acc as object)) {
              return (acc as Record<string, unknown>)[key];
            }
            return undefined;
          }, claims);
        }
        const known = [
          "admin", "analyst", "regional_ops_lead", "store_manager",
          "hr_sensitive", "food_safety_risk", "reviewer", "supply_chain",
        ];
        const list = Array.isArray(raw)
          ? raw.map(String)
          : typeof raw === "string"
            ? raw.replace(/,/g, " ").split(/\s+/)
            : [];
        const matched = list.find((r) => known.includes(r));
        if (matched) token.role = matched;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string | undefined;
      session.role = token.role as string | undefined;
      session.provider = token.provider as string | undefined;
      return session;
    },
    async authorized({ auth }) {
      // Used by proxy.ts for route protection.
      // When OIDC is disabled, always allow (static key mode).
      if (!oidcEnabled) return true;
      return Boolean(auth);
    },
  },
  pages: {
    signIn: "/login",
  },
});

export const oidcConfigured = oidcEnabled;
