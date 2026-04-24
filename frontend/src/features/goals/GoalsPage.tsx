import { useState } from "react"
import { Plus } from "lucide-react"
import { useGoals, useGoalKeyResults } from "@/api/hooks/goals"
import { GoalCard } from "./GoalCard"
import { GoalCreateModal } from "./GoalCreateModal"
import type { Goal } from "@/api/hooks/goals"

function GoalCardWrapper({ goal }: { goal: Goal }) {
  const { data: krs = [] } = useGoalKeyResults(goal.id)
  const avg =
    krs.length > 0
      ? krs.reduce((sum, kr) => sum + kr.progress_percent, 0) / krs.length
      : 0
  return <GoalCard goal={goal} progressPercent={avg} keyResultsCount={krs.length} />
}

function CardSkeleton() {
  return <div className="h-28 animate-pulse rounded-[6px] bg-surface-3" />
}

export function GoalsPage() {
  const [createOpen, setCreateOpen] = useState(false)
  const { data: goals = [], isLoading, isError } = useGoals()

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-semibold text-foreground">Goals</h1>
          <span className="font-mono text-[11px] text-muted-foreground">
            {isLoading ? "…" : goals.length}
          </span>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="flex h-7 items-center gap-1.5 rounded-[5px] border border-border bg-surface-2 px-3 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
        >
          <Plus className="h-3 w-3" />
          New goal
        </button>
      </div>

      {isError && (
        <p className="text-[11px] text-destructive">
          Failed to load goals. Is the backend running?
        </p>
      )}

      {isLoading && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => <CardSkeleton key={i} />)}
        </div>
      )}

      {!isLoading && !isError && goals.length === 0 && (
        <p className="py-12 text-center text-[11px] text-muted-foreground">No goals yet.</p>
      )}

      {!isLoading && !isError && goals.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {goals.map((goal) => (
            <GoalCardWrapper key={goal.id} goal={goal} />
          ))}
        </div>
      )}

      <GoalCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  )
}
