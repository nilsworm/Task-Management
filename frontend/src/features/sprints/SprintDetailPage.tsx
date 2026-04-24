import { useParams, useNavigate } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import { useSprint, useSprintTasks, useStartSprint, useCompleteSprint } from "@/api/hooks/sprints"
import { SprintStatusBadge } from "./SprintStatusBadge"
import { KanbanBoard } from "./KanbanBoard"
import { SprintAssignTask } from "./SprintAssignTask"

export function SprintDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: sprint, isLoading, isError } = useSprint(id!)
  const { data: tasks = [] } = useSprintTasks(id!)
  const start    = useStartSprint()
  const complete = useCompleteSprint()

  if (isLoading) return <p className="font-mono text-[11px] text-muted-foreground">Loading sprint…</p>
  if (isError || !sprint) {
    return <p className="font-mono text-[11px] text-destructive">Sprint not found.</p>
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Header row */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/sprints")}
          className="flex h-7 w-7 items-center justify-center rounded-[5px] border border-border bg-surface-2 text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
          aria-label="Back to sprints"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
        </button>

        <h1 className="flex-1 text-sm font-semibold text-foreground">{sprint.name}</h1>
        <SprintStatusBadge status={sprint.status} />

        <span className="font-mono text-[10px] text-muted-foreground">
          {sprint.start_date} → {sprint.end_date}
        </span>
      </div>

      {/* Goal banner */}
      {sprint.goal && (
        <div className="rounded-[5px] border border-border bg-surface-2 px-3 py-2">
          <span className="font-mono text-[10px] text-muted-foreground">Goal · </span>
          <span className="text-[11px] text-foreground">{sprint.goal}</span>
        </div>
      )}

      {/* Controls */}
      {(sprint.status === "planned" || sprint.status === "active") && (
        <div className="flex items-center gap-2">
          {sprint.status === "planned" && (
            <button
              disabled={start.isPending}
              onClick={() => start.mutate(sprint.id)}
              className="h-7 rounded-[5px] border border-border bg-surface-2 px-3 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground disabled:opacity-50"
            >
              Start sprint
            </button>
          )}
          {sprint.status === "active" && (
            <button
              disabled={complete.isPending}
              onClick={() => complete.mutate(sprint.id)}
              className="h-7 rounded-[5px] border border-border bg-surface-2 px-3 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground disabled:opacity-50"
            >
              Complete sprint
            </button>
          )}
          <SprintAssignTask sprintId={sprint.id} assignedTaskIds={sprint.task_ids} />
        </div>
      )}

      {/* Board */}
      {tasks.length === 0 ? (
        <p className="py-12 text-center text-[11px] text-muted-foreground">
          No tasks in this sprint yet.
        </p>
      ) : (
        <KanbanBoard tasks={tasks} />
      )}
    </div>
  )
}
