import { signIn, auth, oidcConfigured } from "@/auth";
import { redirect } from "next/navigation";

export default async function LoginPage() {
  if (!oidcConfigured) {
    // No OIDC configured — skip login and go straight in.
    redirect("/overview");
  }
  const session = await auth();
  if (session) redirect("/overview");

  return (
    <main className="flex min-h-dvh items-center justify-center px-6">
      <div className="w-full max-w-sm text-center">
        <h1 className="text-2xl font-semibold tracking-tight">StoreSignal AI</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Sign in to continue.
        </p>
        <form
          action={async () => {
            "use server";
            await signIn("storesignal-oidc", { redirectTo: "/overview" });
          }}
          className="mt-8"
        >
          <button
            type="submit"
            className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Sign in with SSO
          </button>
        </form>
      </div>
    </main>
  );
}
