import Link from "next/link";
import { PageTransition } from "./page-transition";
import {
  LayoutDashboard,
  ListChecks,
  Bell,
  TrendingUp,
  Store,
  CheckCircle2,
  FileText,
  Upload,
  Activity,
  Settings as SettingsIcon,
  ScrollText,
} from "lucide-react";

const NAV_WORKSPACE = [
  { href: "/overview",  label: "Overview",  Icon: LayoutDashboard },
  { href: "/incidents", label: "Incidents", Icon: ListChecks },
  { href: "/alerts",    label: "Alerts",    Icon: Bell },
  { href: "/trends",    label: "Trends",    Icon: TrendingUp },
  { href: "/stores",    label: "Stores",    Icon: Store },
  { href: "/actions",   label: "Actions",   Icon: CheckCircle2 },
  { href: "/reports",   label: "Reports",   Icon: FileText },
] as const;

const NAV_DATA = [
  { href: "/import",      label: "Import",      Icon: Upload },
  { href: "/data-health", label: "Data Health", Icon: Activity },
  { href: "/settings",    label: "Settings",    Icon: SettingsIcon },
  { href: "/audit",       label: "Audit",       Icon: ScrollText },
] as const;

const MOBILE = [
  { href: "/overview",  label: "Home",      Icon: LayoutDashboard },
  { href: "/incidents", label: "Incidents", Icon: ListChecks },
  { href: "/alerts",    label: "Alerts",    Icon: Bell },
  { href: "/reports",   label: "Reports",   Icon: FileText },
  { href: "/settings",  label: "More",      Icon: SettingsIcon },
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
          {NAV_WORKSPACE.map(({ href, label, Icon }) => {
            const on = active === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={on ? "page" : undefined}
                className={"nav-link" + (on ? " is-active" : "")}
              >
                <span className="nav-icon" aria-hidden>
                  <Icon size={15} strokeWidth={2} />
                </span>
                <span>{label}</span>
              </Link>
            );
          })}

          <div className="sidebar-section">Data</div>
          {NAV_DATA.map(({ href, label, Icon }) => {
            const on = active === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={on ? "page" : undefined}
                className={"nav-link" + (on ? " is-active" : "")}
              >
                <span className="nav-icon" aria-hidden>
                  <Icon size={15} strokeWidth={2} />
                </span>
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          Local · Demo mode
          <br />
          <strong style={{ color: "var(--fg-2)" }}>SIMULATED DATA</strong>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <h1 className="topbar-title">{title}</h1>
        </header>

        <main className="content"><PageTransition>{children}</PageTransition></main>
      </div>

      <nav className="mobile-nav" aria-label="Primary mobile">
        {MOBILE.map(({ href, label, Icon }) => {
          const on = active === href;
          return (
            <Link
              key={href}
              href={href}
              aria-current={on ? "page" : undefined}
              className={on ? "is-active" : ""}
            >
              <Icon size={18} strokeWidth={2} />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
