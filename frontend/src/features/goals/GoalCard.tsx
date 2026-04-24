import { useNavigate } from "react-router-dom"
import { useDeleteGoal } from "@/api/hooks/goals"
import type { Goal } from "@/api/hooks/goals"
import { toast } from "sonner"

const PRIORITY_COLORS: Record<string, string> = {
  low:      "#9090b0",
  medium:   "#a78bfa",
  high:     "#ffd166",
  critical: "#ff4d6d",
}

interface Props {
  goal: Goal
  progressPercent: number
  keyResultsCount: number
}

export function GoalCard({ goal, progressPercent, keyResultsCount }: Props) {
  const navigate = useNavigate()
  const del = useDeleteGoal()
  const pct = Math.min(Math.max(progressPercent, 0), 100)
  const color = PRIORITY_COLORS[goal.priority] ?? "#9090b0"

  return (
    <div
      className="flex cursor-pointer flex-col gap-2.5 rounded-[6px] border border-border bg-surface-2 p-3.5 transition-colors hover:bg-surface-3"
      onClick={() => navigate(`/goals/${goal.id}`)}
    >
      {/* Title + priority */}
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-semibold leading-snug text-foreground">{goal.title}</span>
        <span
          className="shrink-0 rounded-[3px] px-1.5 py-0.5 font-mono text-[10px] font-semibold"
          style={{ background: `${color}22`, color }}
        >
          {goal.priority}
        </span>
      </div>

      {/* Progress bar */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] text-muted-foreground">
            {keyResultsCount} key result{keyResultsCount !== 1 ? "s" : ""}
          </span>
          <span className="font-mono text-[10px] font-bold" style={{ color }}>
            {pct.toFixed(0)}%
          </span>
        </div>
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
          />
        </div>
      </div>

      {/* Delete action */}
      <div onClick={(e) => e.stopPropagation()} className="border-t border-border pt-2.5">
        <button
          disabled={del.isPending}
          onClick={() => del.mutate(goal.id, {
            onSuccess: () => toast.success("Goal deleted"),
            onError:   () => toast.error("Failed to delete goal"),
          })}
          className="font-mono text-[10px] text-destructive/70 transition-colors hover:text-destructive disabled:opacity-50"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
