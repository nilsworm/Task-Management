import { NavLink, Outlet } from "react-router-dom"
import { LayoutDashboard, CheckSquare, Zap, Target, Wallet } from "lucide-react"
import { ThemeToggle } from "@/components/shared/ThemeToggle"
import { ErrorBoundary } from "@/components/shared/ErrorBoundary"
import { useMetrics } from "@/api/hooks/dashboard"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { to: "/",       label: "Dashboard",       icon: LayoutDashboard, end: true  },
  { to: "/tasks",  label: "Tasks",           icon: CheckSquare,     end: false },
  { to: "/sprints",label: "Sprints",         icon: Zap,             end: false },
  { to: "/goals",  label: "Goals",           icon: Target,          end: false },
  { to: "/cost",   label: "Cost Management", icon: Wallet,          end: false },
]

function LogoMark() {
  return (
    <div
      style={{
        width: 24, height: 24, borderRadius: 5, flexShrink: 0,
        background: "linear-gradient(135deg, #00d4ff, rgba(0,212,255,0.4))",
        display: "flex", alignItems: "center", justifyContent: "center",
        boxShadow: "0 0 12px rgba(0,212,255,0.3)",
      }}
      aria-hidden
    >
      <span style={{ fontSize: 11, fontWeight: 800, color: "#000", fontFamily: "var(--font-mono)", lineHeight: 1 }}>
        PD
      </span>
    </div>
  )
}

function GlobalStats() {
  const { data } = useMetrics()
  const inProgress = data?.task_counts.in_progress ?? 0
  const done = data?.task_counts.done ?? 0

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-cyan" />
        <span className="font-mono text-[11px] text-muted-foreground">
          {inProgress} in progress
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-green" />
        <span className="font-mono text-[11px] text-muted-foreground">
          {done} done
        </span>
      </div>
    </div>
  )
}

function CurrentDate() {
  const formatted = new Date().toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  })
  return (
    <span className="rounded bg-surface-3 border border-border px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
      {formatted}
    </span>
  )
}

export function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">

      {/* ── Sidebar ──────────────────────────────────────────────── */}
      <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-surface-1">

        {/* Logo */}
        <div className="flex h-12 shrink-0 items-center gap-2 px-4">
          <LogoMark />
          <span className="text-sm font-bold tracking-[0.3px] text-foreground">
            devflow
          </span>
        </div>

        <div className="mx-3 h-px bg-border" />

        {/* Nav */}
        <nav className="flex flex-col gap-0.5 p-2">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-1.5 rounded-[5px] border px-3 py-[7px] text-xs font-medium transition-all duration-150",
                  isActive
                    ? "border-cyan/20 bg-cyan/10 text-cyan"
                    : "border-transparent text-muted-foreground hover:bg-surface-3 hover:text-foreground",
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className="shrink-0 transition-opacity"
                    style={{ width: 13, height: 13, opacity: isActive ? 0.9 : 0.7 }}
                  />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* ── Main ─────────────────────────────────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden">

        {/* Header */}
        <header className="flex h-12 shrink-0 items-center justify-end gap-3 border-b border-border bg-surface-1 px-4">
          <GlobalStats />
          <div className="h-[18px] w-px bg-border" />
          <CurrentDate />
          <div className="h-[18px] w-px bg-border" />
          <ThemeToggle />
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-3">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

    </div>
  )
}
