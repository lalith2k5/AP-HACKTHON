import { DefaultSession } from "next-auth";

// Module augmentation: tell Auth.js about our custom session/JWT fields.
// Without this, `session.accessToken`, `session.role`, etc. fail type check.
// Runtime is unaffected — this is purely a TypeScript shape declaration.

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    role?: string;
    provider?: string;
    user: DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    expiresAt?: number;
    role?: string;
    provider?: string;
  }
}
