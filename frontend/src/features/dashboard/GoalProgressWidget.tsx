import type { GoalProgressData } from "@/api/hooks/dashboard"

interface Props {
  goalProgress: GoalProgressData
}

export function GoalProgressWidget({ goalProgress }: Props) {
  const { goals } = goalProgress

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <h2 className="text-sm font-semibold">Goal Progress</h2>

      {goals.length === 0 ? (
        <p className="py-4 text-center text-xs text-muted-foreground">No goals yet.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {goals.map((g) => {
            const pct = Math.min(Math.max(g.progress_percent, 0), 100)
            return (
              <div key={g.goal_id} className="flex flex-col gap-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium truncate">{g.goal_title}</span>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {pct.toFixed(0)}%
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{ width: `${pct}%` }}
                    role="progressbar"
                    aria-valuenow={pct}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={g.goal_title}
                  />
                </div>
                <span className="text-xs text-muted-foreground">
                  {g.key_results_count} key result{g.key_results_count !== 1 ? "s" : ""}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
