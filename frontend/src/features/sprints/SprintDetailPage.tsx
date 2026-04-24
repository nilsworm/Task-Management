import { useParams, useNavigate } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useSprint, useSprintTasks, useStartSprint, useCompleteSprint } from "@/api/hooks/sprints"
import { SprintStatusBadge } from "./SprintStatusBadge"
import { KanbanBoard } from "./KanbanBoard"
import { SprintAssignTask } from "./SprintAssignTask"

export function SprintDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: sprint, isLoading, isError } = useSprint(id!)
  const { data: tasks = [] } = useSprintTasks(id!)
  const start = useStartSprint()
  const complete = useCompleteSprint()

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading sprint…</p>
  if (isError || !sprint) {
    return <p className="text-sm text-destructive">Sprint not found.</p>
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/sprints")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex flex-1 items-center gap-3">
          <h1 className="text-2xl font-bold">{sprint.name}</h1>
          <SprintStatusBadge status={sprint.status} />
        </div>
        <p className="text-sm text-muted-foreground">
          {sprint.start_date} → {sprint.end_date}
        </p>
        {sprint.status === "planned" && (
          <Button
            size="sm"
            disabled={start.isPending}
            onClick={() => start.mutate(sprint.id)}
          >
            Start Sprint
          </Button>
        )}
        {sprint.status === "active" && (
          <Button
            size="sm"
            variant="outline"
            disabled={complete.isPending}
            onClick={() => complete.mutate(sprint.id)}
          >
            Complete Sprint
          </Button>
        )}
        {(sprint.status === "planned" || sprint.status === "active") && (
          <SprintAssignTask sprintId={sprint.id} assignedTaskIds={sprint.task_ids} />
        )}
      </div>

      {tasks.length === 0 ? (
        <p className="py-12 text-center text-sm text-muted-foreground">
          No tasks in this sprint yet.
        </p>
      ) : (
        <KanbanBoard tasks={tasks} />
      )}
    </div>
  )
}
