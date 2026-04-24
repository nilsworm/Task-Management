import { useState } from "react"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useGoals, useGoalKeyResults } from "@/api/hooks/goals"
import { GoalCard } from "./GoalCard"
import { GoalCreateModal } from "./GoalCreateModal"
import { Skeleton } from "@/components/ui/skeleton"
import type { Goal } from "@/api/hooks/goals"

function GoalCardWrapper({ goal }: { goal: Goal }) {
  const { data: krs = [] } = useGoalKeyResults(goal.id)
  const avg =
    krs.length > 0
      ? krs.reduce((sum, kr) => sum + kr.progress_percent, 0) / krs.length
      : 0
  return <GoalCard goal={goal} progressPercent={avg} keyResultsCount={krs.length} />
}

export function GoalsPage() {
  const [createOpen, setCreateOpen] = useState(false)
  const { data: goals = [], isLoading, isError } = useGoals()

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Goals</h1>
          <p className="text-sm text-muted-foreground">
            {isLoading ? "Loading…" : `${goals.length} goal${goals.length !== 1 ? "s" : ""}`}
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Goal
        </Button>
      </div>

      {isError && (
        <p className="text-sm text-destructive">Failed to load goals. Is the backend running?</p>
      )}

      {!isLoading && !isError && goals.length === 0 && (
        <p className="py-12 text-center text-sm text-muted-foreground">
          No goals yet. Create one to get started.
        </p>
      )}

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-40 w-full" />)}
        </div>
      )}

      {!isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {goals.map((goal) => (
            <GoalCardWrapper key={goal.id} goal={goal} />
          ))}
        </div>
      )}

      <GoalCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  )
}
