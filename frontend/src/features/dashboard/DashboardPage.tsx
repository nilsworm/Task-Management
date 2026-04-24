import { useDashboard, useMetrics, useBurndown, useVelocity, useGoalProgress } from "@/api/hooks/dashboard"
import { MetricsWidget } from "./MetricsWidget"
import { BurndownWidget } from "./BurndownWidget"
import { VelocityWidget } from "./VelocityWidget"
import { GoalProgressWidget } from "./GoalProgressWidget"

function WidgetSkeleton() {
  return <div className="h-64 animate-pulse rounded-[6px] bg-surface-3" />
}

export function DashboardPage() {
  const dashboard = useDashboard()
  const metrics   = useMetrics()
  const burndown  = useBurndown()
  const velocity  = useVelocity()
  const goalProgress = useGoalProgress()

  const activeSprint = dashboard.data?.active_sprint

  return (
    <div className="flex flex-col gap-3">
      <h1 className="sr-only">Dashboard</h1>

      {/* Active sprint strip */}
      {activeSprint && (
        <div className="flex items-center gap-2 rounded-[5px] border border-border bg-surface-2 px-3 py-2">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-cyan" />
          <span className="font-mono text-[11px] text-muted-foreground">Active sprint</span>
          <span className="text-xs font-semibold text-foreground">{activeSprint.name}</span>
          <span className="ml-auto font-mono text-[11px] text-muted-foreground">
            {activeSprint.completion_percent}% done
          </span>
        </div>
      )}

      {/* 2×2 widget grid */}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {metrics.isLoading || !metrics.data ? (
          <WidgetSkeleton />
        ) : (
          <MetricsWidget metrics={metrics.data} />
        )}

        {burndown.isLoading ? (
          <WidgetSkeleton />
        ) : burndown.isError || !burndown.data ? (
          <div className="flex items-center justify-center rounded-[6px] border border-border bg-surface-2 p-5">
            <p className="text-[11px] text-muted-foreground">No active sprint — no burndown to display.</p>
          </div>
        ) : (
          <BurndownWidget burndown={burndown.data} />
        )}

        {velocity.isLoading || !velocity.data ? (
          <WidgetSkeleton />
        ) : (
          <VelocityWidget velocity={velocity.data} />
        )}

        {goalProgress.isLoading || !goalProgress.data ? (
          <WidgetSkeleton />
        ) : (
          <GoalProgressWidget goalProgress={goalProgress.data} />
        )}
      </div>
    </div>
  )
}
