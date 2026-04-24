import { useDashboard, useMetrics, useBurndown, useVelocity, useGoalProgress } from "@/api/hooks/dashboard"
import { MetricsWidget } from "./MetricsWidget"
import { BurndownWidget } from "./BurndownWidget"
import { VelocityWidget } from "./VelocityWidget"
import { GoalProgressWidget } from "./GoalProgressWidget"

function Skeleton() {
  return <div className="h-64 animate-pulse rounded-xl bg-muted" />
}

export function DashboardPage() {
  const dashboard = useDashboard()
  const metrics = useMetrics()
  const burndown = useBurndown()
  const velocity = useVelocity()
  const goalProgress = useGoalProgress()

  const activeSprint = dashboard.data?.active_sprint

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        {activeSprint ? (
          <p className="text-sm text-muted-foreground">
            Active sprint:{" "}
            <span className="font-medium text-foreground">{activeSprint.name}</span>
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">No active sprint.</p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {metrics.isLoading || !metrics.data ? (
          <Skeleton />
        ) : (
          <MetricsWidget metrics={metrics.data} />
        )}

        {burndown.isLoading ? (
          <Skeleton />
        ) : burndown.isError || !burndown.data ? (
          <div className="flex items-center justify-center rounded-xl border border-border bg-card p-5">
            <p className="text-sm text-muted-foreground">
              No active sprint to display burndown.
            </p>
          </div>
        ) : (
          <BurndownWidget burndown={burndown.data} />
        )}

        {velocity.isLoading || !velocity.data ? (
          <Skeleton />
        ) : (
          <VelocityWidget velocity={velocity.data} />
        )}

        {goalProgress.isLoading || !goalProgress.data ? (
          <Skeleton />
        ) : (
          <GoalProgressWidget goalProgress={goalProgress.data} />
        )}
      </div>
    </div>
  )
}
