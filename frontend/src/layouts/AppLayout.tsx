import { NavLink, Outlet } from "react-router-dom"
import {
  LayoutDashboard,
  CheckSquare,
  Zap,
  Target,
} from "lucide-react"
import { Separator } from "@/components/ui/separator"
import { ThemeToggle } from "@/components/shared/ThemeToggle"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/tasks", label: "Tasks", icon: CheckSquare, end: false },
  { to: "/sprints", label: "Sprints", icon: Zap, end: false },
  { to: "/goals", label: "Goals", icon: Target, end: false },
]

export function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {/* Sidebar */}
      <aside className="flex w-60 flex-col border-r border-border bg-card">
        <div className="flex h-14 items-center px-4">
          <span className="text-sm font-semibold tracking-tight">Task Manager</span>
        </div>
        <Separator />
        <nav className="flex flex-col gap-1 p-2">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-6">
          <span className="text-sm text-muted-foreground">Personal Task Management</span>
          <ThemeToggle />
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
