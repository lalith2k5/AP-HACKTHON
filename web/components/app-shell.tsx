import Link from "next/link";

const NAV = [
  { href: "/overview", label: "Overview",  icon: "◎" },
  { href: "/incidents", label: "Incidents", icon: "▦" },
  { href: "/alerts",    label: "Alerts",    icon: "!" },
  { href: "/reports",   label: "Reports",   icon: "▤" },
] as const;

export function AppShell({
  children,
  active,
  title,
}: {
  children: React.ReactNode;
  active: string;
  title: string;
}) {
  return (
    <div className="flex min-h-dvh">
      {/* Sidebar — backdrop-blur material */}
      <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 border-r border-border bg-background/70 backdrop-blur-xl md:flex md:flex-col">
        <div className="flex h-14 items-center gap-2 px-5">
          <span
            aria-hidden
            className="inline-block size-2.5 rounded-full bg-[var(--primary)] shadow-[0_0_10px_var(--primary)]"
          />
          <span className="text-sm font-semibold tracking-tight">StoreSignal</span>
        </div>
        <nav className="flex-1 space-y-0.5 px-3 py-2">
          {NAV.map((n) => {
            const on = active === n.href;
            return (
              <Link
                key={n.href}
                href={n.href}
                className={
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors " +
                  (on
                    ? "bg-[color-mix(in_oklch,var(--primary),transparent_88%)] text-[var(--primary)]"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground")
                }
              >
                <span aria-hidden className="w-4 text-center opacity-80">{n.icon}</span>
                {n.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-border px-5 py-3 text-[11px] leading-relaxed text-muted-foreground">
          Local · Demo mode
          <br />
          SIMULATED DATA
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-14 items-center gap-3 border-b border-border bg-background/70 px-5 backdrop-blur-xl">
          <span className="text-sm font-semibold tracking-tight md:hidden">StoreSignal</span>
          <h1 className="text-sm font-medium tracking-tight text-muted-foreground">{title}</h1>
        </header>
        <main className="flex-1 px-5 py-6">{children}</main>
      </div>
    </div>
  );
}
