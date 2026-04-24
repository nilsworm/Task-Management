import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { ArrowLeft, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useGoal, useGoalKeyResults } from "@/api/hooks/goals"
import { KeyResultItem } from "./KeyResultItem"
import { KeyResultCreateModal } from "./KeyResultCreateModal"
import { KeyResultEditModal } from "./KeyResultEditModal"
import type { KeyResult } from "@/api/hooks/goals"

export function GoalDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: goal, isLoading, isError } = useGoal(id!)
  const { data: krs = [] } = useGoalKeyResults(id!)
  const [createOpen, setCreateOpen] = useState(false)
  const [editKr, setEditKr] = useState<KeyResult | null>(null)

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading goal…</p>
  if (isError || !goal) return <p className="text-sm text-destructive">Goal not found.</p>

  const avgProgress =
    krs.length > 0
      ? krs.reduce((s, kr) => s + kr.progress_percent, 0) / krs.length
      : 0
  const clamped = Math.min(Math.max(avgProgress, 0), 100)

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/goals")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{goal.title}</h1>
          <p className="text-sm text-muted-foreground capitalize">{goal.priority} priority</p>
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Overall Progress</span>
          <span>{clamped.toFixed(0)}%</span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${clamped}%` }}
            role="progressbar"
            aria-valuenow={clamped}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>

      <Separator />

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          Key Results
          <span className="ml-2 text-sm font-normal text-muted-foreground">({krs.length})</span>
        </h2>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-3.5 w-3.5" />
          Add KR
        </Button>
      </div>

      {krs.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No key results yet. Add one to track progress.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {krs.map((kr) => (
            <KeyResultItem key={kr.id} kr={kr} onEdit={setEditKr} />
          ))}
        </div>
      )}

      <KeyResultCreateModal
        goalId={id!}
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />
      <KeyResultEditModal
        key={editKr?.id ?? ""}
        goalId={id!}
        kr={editKr}
        onClose={() => setEditKr(null)}
      />
    </div>
  )
}
