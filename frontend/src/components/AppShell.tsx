import { NavLink } from "react-router-dom";
import {
  Blocks,
  BookOpenText,
  Braces,
  LayoutDashboard,
  Settings,
  Share2,
  Sparkles,
  UserRound,
} from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { to: "/setup", label: "Persona interview", icon: Sparkles },
  { to: "/context", label: "Persona core", icon: UserRound },
  { to: "/projects", label: "Project holders", icon: Blocks },
  { to: "/playground", label: "MCP playground", icon: Braces },
  { to: "/share", label: "Persona pass", icon: Share2 },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground" data-testid="skipti-app-shell">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-border bg-[#100e0e] p-6 lg:flex lg:flex-col" data-testid="desktop-navigation-sidebar">
        <NavLink to="/dashboard" className="mb-12 block" data-testid="sidebar-skipti-logo-link">
          <div className="flex items-center gap-3">
            <div className="grid size-9 place-items-center border border-[#6e0d25] bg-[#1b0c10]" data-testid="sidebar-logo-mark"><BookOpenText className="size-4 text-[#d7a0b1]" /></div>
            <div>
              <p className="font-heading text-2xl leading-none" data-testid="sidebar-product-name">Skipti AI</p>
              <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.22em] text-muted-foreground" data-testid="sidebar-protocol-label">Context infrastructure</p>
            </div>
          </div>
        </NavLink>
        <nav className="space-y-1" data-testid="sidebar-navigation-list">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                data-testid={`sidebar-${item.label.toLowerCase().replaceAll(" ", "-")}-link`}
                className={({ isActive }) => cn("group flex items-center gap-3 border-l px-3 py-3 text-sm text-muted-foreground transition-[color,background-color,border-color] duration-200 hover:border-[#6e0d25] hover:bg-[#1c1917] hover:text-foreground", isActive ? "border-[#872c4c] bg-[#1c1416] text-foreground" : "border-transparent")}
              >
                <Icon className="size-4" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
        <div className="mt-auto border border-border bg-[#151313] p-4" data-testid="sidebar-owner-card">
          <div className="mb-2 flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground" data-testid="sidebar-owner-mode">Demo owner</span>
            <span className="size-1.5 animate-status-pulse rounded-full bg-emerald-400" data-testid="sidebar-connection-indicator" />
          </div>
          <p className="text-sm font-medium" data-testid="sidebar-owner-name">Alex Morgan</p>
          <p className="mt-1 text-xs text-muted-foreground" data-testid="sidebar-owner-email">demo@skipti.ai</p>
        </div>
      </aside>
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-[#0c0a09]/90 px-5 backdrop-blur-xl lg:hidden" data-testid="mobile-header">
        <NavLink to="/dashboard" className="font-heading text-2xl" data-testid="mobile-logo-link">Skipti</NavLink>
        <NavLink to="/playground" className="border border-[#6e0d25] px-3 py-2 font-mono text-[10px] uppercase tracking-widest" data-testid="mobile-playground-link">Playground</NavLink>
      </header>
      <main className="relative z-10 px-5 py-8 lg:ml-72 lg:px-12 lg:py-10" data-testid="app-main-content">{children}</main>
      <nav className="fixed inset-x-0 bottom-0 z-50 grid grid-cols-5 border-t border-border bg-[#100e0e]/95 px-2 py-2 backdrop-blur-xl lg:hidden" data-testid="mobile-bottom-navigation">
        {nav.slice(0, 5).map((item) => {
          const Icon = item.icon;
          return <NavLink key={item.to} to={item.to} className={({ isActive }) => cn("flex flex-col items-center gap-1 py-1 text-[9px] text-muted-foreground", isActive && "text-[#d7a0b1]")} data-testid={`mobile-${item.label.toLowerCase().replaceAll(" ", "-")}-link`}><Icon className="size-4" />{item.label.split(" ")[0]}</NavLink>;
        })}
      </nav>
    </div>
  );
}

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return (
    <header className="mb-9 flex flex-col gap-6 border-b border-border pb-8 md:flex-row md:items-end md:justify-between" data-testid={`${eyebrow.toLowerCase().replaceAll(" ", "-")}-page-header`}>
      <div className="max-w-3xl">
        <p className="mb-3 font-mono text-[10px] uppercase tracking-[0.28em] text-[#c47a91]" data-testid="page-header-eyebrow">{eyebrow}</p>
        <h1 className="font-heading text-5xl font-light tracking-tight md:text-6xl" data-testid="page-header-title">{title}</h1>
        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground" data-testid="page-header-description">{description}</p>
      </div>
      {action ? <div data-testid="page-header-action">{action}</div> : null}
    </header>
  );
}

export function StatusPill({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "brand" | "good" | "warning" }) {
  const tones = { neutral: "border-border text-muted-foreground", brand: "border-[#6e0d25] bg-[#1d0b10] text-[#e0a7b8]", good: "border-emerald-900 bg-emerald-950/40 text-emerald-300", warning: "border-amber-900 bg-amber-950/30 text-amber-300" };
  return <span className={cn("inline-flex items-center border px-2 py-1 font-mono text-[9px] uppercase tracking-[0.14em]", tones[tone])}>{children}</span>;
}