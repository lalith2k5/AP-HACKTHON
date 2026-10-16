import Link from "next/link";

const NAV = [
  { href: "/overview",    label: "Overview",    icon: "\u25CE" },
  { href: "/incidents",   label: "Incidents",   icon: "\u25A6" },
  { href: "/alerts",      label: "Alerts",      icon: "\u25CF" },
  { href: "/trends",      label: "Trends",      icon: "\u223F" },
  { href: "/stores",      label: "Stores",      icon: "\u25A4" },
  { href: "/actions",     label: "Actions",     icon: "\u2713" },
  { href: "/reports",     label: "Reports",     icon: "\u2263" },
  { href: "/import",      label: "Import",      icon: "\u21E3" },
  { href: "/data-health", label: "Data Health", icon: "\u25D4" },
  { href: "/settings",    label: "Settings",    icon: "\u2699" },
  { href: "/audit",       label: "Audit",       icon: "\u2261" },
] as const;

const MOBILE = [
  { href: "/overview",  label: "Home",      icon: "\u25CE" },
  { href: "/incidents", label: "Incidents", icon: "\u25A6" },
  { href: "/alerts",    label: "Alerts",    icon: "\u25CF" },
  { href: "/reports",   label: "Reports",   icon: "\u2263" },
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
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="sidebar-brand-dot" aria-hidden />
          <span className="sidebar-brand-name">StoreSignal</span>
        </div>

        <nav className="sidebar-nav" aria-label="Primary">
          <div className="sidebar-section">Workspace</div>
          {NAV.slice(0, 7).map((n) => {
            const on = active === n.href;
            return (
              <Link
                key={n.href}
                href={n.href}
                aria-current={on ? "page" : undefined}
                className={"nav-link" + (on ? " is-active" : "")}
              >
                <span className="nav-icon" aria-hidden>{n.icon}</span>
                <span>{n.label}</span>
              </Link>
            );
          })}

          <div className="sidebar-section">Data</div>
          {NAV.slice(7).map((n) => {
            const on = active === n.href;
            return (
              <Link
                key={n.href}
                href={n.href}
                aria-current={on ? "page" : undefined}
                className={"nav-link" + (on ? " is-active" : "")}
              >
                <span className="nav-icon" aria-hidden>{n.icon}</span>
                <span>{n.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          Local · Demo mode
          <br />
          <strong>SIMULATED DATA</strong>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div>
            <div className="topbar-title">{title}</div>
          </div>
        </header>

        <main className="content">{children}</main>
      </div>

      <nav className="mobile-nav" aria-label="Primary mobile">
        {MOBILE.map((n) => {
          const on = active === n.href;
          return (
            <Link
              key={n.href}
              href={n.href}
              aria-current={on ? "page" : undefined}
              className={on ? "is-active" : ""}
            >
              <span className="nav-icon" aria-hidden>{n.icon}</span>
              <span>{n.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
