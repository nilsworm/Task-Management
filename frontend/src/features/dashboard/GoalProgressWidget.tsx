import type { GoalProgressData } from "@/api/hooks/dashboard"

const GOAL_COLORS = ["#00d4ff", "#06d6a0", "#a78bfa", "#fb923c", "#ffd166", "#ff4d6d"]

interface Props { goalProgress: GoalProgressData }

export function GoalProgressWidget({ goalProgress }: Props) {
  const { goals } = goalProgress

  return (
    <div className="flex flex-col gap-3.5 rounded-[6px] border border-border bg-surface-2 p-3.5">
      <span className="text-[11px] font-semibold uppercase tracking-[0.6px] text-muted-foreground">
        Goal Progress
      </span>

      {goals.length === 0 ? (
        <p className="py-8 text-center text-[11px] text-muted-foreground">No goals yet.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {goals.map((g, idx) => {
            const pct = Math.min(Math.max(g.progress_percent, 0), 100)
            const color = GOAL_COLORS[idx % GOAL_COLORS.length]
            return (
              <div key={g.goal_id} className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-xs font-medium text-foreground">{g.goal_title}</span>
                  <span
                    className="shrink-0 font-mono text-[11px] font-bold"
                    style={{ color }}
                  >
                    {pct.toFixed(0)}%
                  </span>
                </div>

                {/* Progress bar */}
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-3">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${pct}%`,
                      background: `linear-gradient(90deg, ${color} 0%, ${color}cc 100%)`,
                      boxShadow: `0 0 8px ${color}60`,
                    }}
                    role="progressbar"
                    aria-valuenow={pct}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={g.goal_title}
                  />
                </div>

                <span className="font-mono text-[10px] text-muted-foreground">
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
