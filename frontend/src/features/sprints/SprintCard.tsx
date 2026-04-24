import { useNavigate } from "react-router-dom"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { SprintStatusBadge } from "./SprintStatusBadge"
import { useStartSprint, useCompleteSprint, useDeleteSprint } from "@/api/hooks/sprints"
import type { Sprint } from "@/api/hooks/sprints"
import { toast } from "sonner"

interface Props {
  sprint: Sprint
}

export function SprintCard({ sprint }: Props) {
  const navigate = useNavigate()
  const start = useStartSprint()
  const complete = useCompleteSprint()
  const del = useDeleteSprint()

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={() => navigate(`/sprints/${sprint.id}`)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{sprint.name}</CardTitle>
          <SprintStatusBadge status={sprint.status} />
        </div>
        <p className="text-xs text-muted-foreground">
          {sprint.start_date} → {sprint.end_date}
        </p>
      </CardHeader>
      <CardContent className="pb-2">
        <p className="text-sm text-muted-foreground">
          {sprint.task_ids.length} task{sprint.task_ids.length !== 1 ? "s" : ""}
        </p>
      </CardContent>
      <CardFooter
        className="flex gap-2"
        onClick={(e) => e.stopPropagation()}
      >
        {sprint.status === "planned" && (
          <Button
            size="sm"
            variant="outline"
            disabled={start.isPending}
            onClick={() =>
              start.mutate(sprint.id, {
                onSuccess: () => toast.success("Sprint started"),
                onError: () => toast.error("Failed to start sprint"),
              })
            }
          >
            Start
          </Button>
        )}
        {sprint.status === "active" && (
          <Button
            size="sm"
            variant="outline"
            disabled={complete.isPending}
            onClick={() =>
              complete.mutate(sprint.id, {
                onSuccess: () => toast.success("Sprint completed"),
                onError: () => toast.error("Failed to complete sprint"),
              })
            }
          >
            Complete
          </Button>
        )}
        {sprint.status !== "active" && (
          <Button
            size="sm"
            variant="ghost"
            className="text-destructive hover:text-destructive"
            disabled={del.isPending}
            onClick={() =>
              del.mutate(sprint.id, {
                onSuccess: () => toast.success("Sprint deleted"),
                onError: () => toast.error("Failed to delete sprint"),
              })
            }
          >
            Delete
          </Button>
        )}
      </CardFooter>
    </Card>
  )
}
