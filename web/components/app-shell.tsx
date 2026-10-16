import Link from "next/link";

const NAV = [
  { href: "/overview",    label: "Overview",    icon: "\u25CE" },
  { href: "/incidents",   label: "Incidents",   icon: "\u25A6" },
  { href: "/alerts",      label: "Alerts",      icon: "!" },
  { href: "/trends",      label: "Trends",      icon: "\u223F" },
  { href: "/stores",      label: "Stores",      icon: "\u25A4" },
  { href: "/actions",     label: "Actions",     icon: "\u2713" },
  { href: "/reports",     label: "Reports",     icon: "\u25A4" },
  { href: "/import",      label: "Import",      icon: "\u21E3" },
  { href: "/data-health", label: "Data Health", icon: "\u25CB" },
  { href: "/settings",    label: "Settings",    icon: "\u2699" },
  { href: "/audit",       label: "Audit",       icon: "\u2261" },
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
    <div className="flex min-h-dvh bg-[var(--muted)] dark:bg-[var(--background)]">
      {/* Sidebar — glassmorphic, generous padding */}
      <aside className="sticky top-0 hidden h-dvh w-72 shrink-0 border-r border-[var(--sidebar-border)] bg-[var(--sidebar)] backdrop-blur-2xl md:flex md:flex-col">
        <div className="flex h-20 items-center gap-3 px-7">
          <span
            aria-hidden
            className="inline-block size-2.5 rounded-full bg-[var(--primary)] shadow-[0_0_12px_var(--primary)]"
          />
          <span className="text-[15px] font-semibold tracking-tight">StoreSignal</span>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-4">
          {NAV.map((n) => {
            const on = active === n.href;
            return (
              <Link
                key={n.href}
                href={n.href}
                className={
                  "press flex items-center gap-3 rounded-2xl px-4 py-3 text-[14px] font-medium " +
                  (on
                    ? "bg-[color-mix(in_oklch,var(--primary),transparent_90%)] text-[var(--primary)]"
                    : "text-[var(--muted-foreground)] hover:bg-[color-mix(in_oklch,var(--foreground),transparent_94%)] hover:text-foreground")
                }
              >
                <span aria-hidden className="w-5 text-center text-[15px] opacity-80">
                  {n.icon}
                </span>
                {n.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-[var(--sidebar-border)] px-7 py-5 text-[11px] leading-relaxed text-[var(--muted-foreground)]">
          Local · Demo mode
          <br />
          <span className="font-medium">SIMULATED DATA</span>
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-20 items-center gap-4 border-b border-[var(--border)] bg-[color-mix(in_oklch,var(--background),transparent_25%)] px-8 backdrop-blur-2xl">
          <span className="text-[15px] font-semibold tracking-tight md:hidden">StoreSignal</span>
          <h1 className="text-[15px] font-medium tracking-tight text-[var(--muted-foreground)]">
            {title}
          </h1>
        </header>

        <main className="flex-1 px-8 py-10 md:px-12 md:py-14">
          <div className="mx-auto max-w-[1400px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
