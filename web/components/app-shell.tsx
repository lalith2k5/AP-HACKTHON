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

const MOBILE_NAV = [
  { href: "/overview",  label: "Home",      icon: "\u25CE" },
  { href: "/incidents", label: "Incidents", icon: "\u25A6" },
  { href: "/alerts",    label: "Alerts",    icon: "!" },
  { href: "/reports",   label: "Reports",   icon: "\u25A4" },
  { href: "/settings",  label: "More",      icon: "\u2261" },
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
      {/* Sidebar - sticky, solid background (no blur = no jitter) */}
      <aside className="sticky top-0 hidden h-dvh w-72 shrink-0 flex-col border-r border-[var(--sidebar-border)] bg-[var(--sidebar-solid)] md:flex">
        <div className="flex h-20 shrink-0 items-center gap-3 px-7">
          <span className="inline-block size-2.5 rounded-full bg-[var(--primary)]" aria-hidden />
          <span className="text-[15px] font-semibold tracking-tight">StoreSignal</span>
        </div>

        <nav className="sidebar-scroll flex-1 space-y-1 px-4 py-4" aria-label="Primary">
          {NAV.map((n) => {
            const on = active === n.href;
            return (
              <Link
                key={n.href}
                href={n.href}
                aria-current={on ? "page" : undefined}
                className={"nav-link" + (on ? " is-active" : "")}
              >
                <span aria-hidden className="w-5 text-center text-[15px] opacity-90">
                  {n.icon}
                </span>
                <span>{n.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="shrink-0 border-t border-[var(--sidebar-border)] px-7 py-5 text-[11px] leading-relaxed text-[var(--muted-foreground)]">
          Local · Demo mode
          <br />
          <span className="font-medium">SIMULATED DATA</span>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="header-material sticky top-0 z-30 flex h-16 items-center px-4 md:h-20 md:px-8">
          <span className="text-[14px] font-semibold tracking-tight md:hidden">StoreSignal</span>
          <h1 className="hidden text-[15px] font-medium tracking-tight text-[var(--muted-foreground)] md:block">
            {title}
          </h1>
          <h1 className="ml-auto text-[13px] font-medium tracking-tight text-[var(--muted-foreground)] md:hidden">
            {title}
          </h1>
        </header>

        <main className="flex-1 px-4 pb-28 pt-6 md:px-12 md:pb-14 md:pt-12">
          <div className="mx-auto max-w-[1400px]">{children}</div>
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav
        aria-label="Primary mobile"
        className="header-material fixed inset-x-0 bottom-0 z-40 flex h-20 items-stretch justify-around px-2 pb-[max(env(safe-area-inset-bottom),8px)] md:hidden"
      >
        {MOBILE_NAV.map((n) => {
          const on = active === n.href;
          return (
            <Link
              key={n.href}
              href={n.href}
              aria-current={on ? "page" : undefined}
              className={
                "press flex flex-1 flex-col items-center justify-center gap-1 rounded-2xl text-[10px] font-medium " +
                (on ? "text-[var(--primary)]" : "text-[var(--muted-foreground)]")
              }
            >
              <span aria-hidden className="text-[18px] leading-none">
                {n.icon}
              </span>
              <span>{n.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
