import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { ArrowLeft, Plus } from "lucide-react"
import { useGoal, useGoalKeyResults } from "@/api/hooks/goals"
import { KeyResultItem } from "./KeyResultItem"
import { KeyResultCreateModal } from "./KeyResultCreateModal"
import { KeyResultEditModal } from "./KeyResultEditModal"
import type { KeyResult } from "@/api/hooks/goals"

const PRIORITY_COLORS: Record<string, string> = {
  low:      "#9090b0",
  medium:   "#a78bfa",
  high:     "#ffd166",
  critical: "#ff4d6d",
}

export function GoalDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: goal, isLoading, isError } = useGoal(id!)
  const { data: krs = [] } = useGoalKeyResults(id!)
  const [createOpen, setCreateOpen] = useState(false)
  const [editKr, setEditKr] = useState<KeyResult | null>(null)

  if (isLoading) return <p className="font-mono text-[11px] text-muted-foreground">Loading goal…</p>
  if (isError || !goal) return <p className="font-mono text-[11px] text-destructive">Goal not found.</p>

  const avgProgress =
    krs.length > 0
      ? krs.reduce((s, kr) => s + kr.progress_percent, 0) / krs.length
      : 0
  const pct = Math.min(Math.max(avgProgress, 0), 100)
  const color = PRIORITY_COLORS[goal.priority] ?? "#9090b0"

  return (
    <div className="flex max-w-2xl flex-col gap-3">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/goals")}
          className="flex h-7 w-7 items-center justify-center rounded-[5px] border border-border bg-surface-2 text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
          aria-label="Back to goals"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
        </button>
        <h1 className="flex-1 text-sm font-semibold text-foreground">{goal.title}</h1>
        <span
          className="rounded-[3px] px-1.5 py-0.5 font-mono text-[10px] font-semibold"
          style={{ background: `${color}22`, color }}
        >
          {goal.priority}
        </span>
      </div>

      {/* Overall progress */}
      <div className="flex flex-col gap-1.5 rounded-[6px] border border-border bg-surface-2 p-3.5">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] text-muted-foreground">Overall Progress</span>
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

      {/* Key Results section */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.6px] text-muted-foreground">
            Key Results
          </span>
          <span className="font-mono text-[10px] text-muted-foreground">({krs.length})</span>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="flex h-6 items-center gap-1.5 rounded-[4px] border border-border bg-surface-2 px-2 font-mono text-[10px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
        >
          <Plus className="h-3 w-3" />
          Add KR
        </button>
      </div>

      {krs.length === 0 ? (
        <p className="py-8 text-center text-[11px] text-muted-foreground">
          No key results yet. Add one to track progress.
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {krs.map((kr) => (
            <KeyResultItem key={kr.id} kr={kr} onEdit={setEditKr} />
          ))}
        </div>
      )}

      <KeyResultCreateModal goalId={id!} open={createOpen} onClose={() => setCreateOpen(false)} />
      <KeyResultEditModal
        key={editKr?.id ?? ""}
        goalId={id!}
        kr={editKr}
        onClose={() => setEditKr(null)}
      />
    </div>
  )
}
