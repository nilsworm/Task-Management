import { useNavigate } from "react-router-dom"
import { SprintStatusBadge } from "./SprintStatusBadge"
import { useStartSprint, useCompleteSprint, useDeleteSprint } from "@/api/hooks/sprints"
import type { Sprint } from "@/api/hooks/sprints"
import { toast } from "sonner"

interface Props { sprint: Sprint }

export function SprintCard({ sprint }: Props) {
  const navigate = useNavigate()
  const start    = useStartSprint()
  const complete = useCompleteSprint()
  const del      = useDeleteSprint()

  return (
    <div
      className="flex cursor-pointer flex-col gap-2.5 rounded-[6px] border border-border bg-surface-2 p-3.5 transition-colors hover:bg-surface-3"
      onClick={() => navigate(`/sprints/${sprint.id}`)}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-semibold text-foreground leading-snug">{sprint.name}</span>
        <SprintStatusBadge status={sprint.status} />
      </div>

      {/* Dates */}
      <span className="font-mono text-[10px] text-muted-foreground">
        {sprint.start_date} → {sprint.end_date}
      </span>

      {/* Goal */}
      {sprint.goal && (
        <p className="line-clamp-2 text-[11px] text-muted-foreground">{sprint.goal}</p>
      )}

      {/* Progress */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1 rounded-full bg-surface-3 overflow-hidden">
          <div
            className="h-full rounded-full bg-green transition-all"
            style={{ width: `${sprint.completion_percent}%` }}
          />
        </div>
        <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
          {sprint.completion_percent}% · {sprint.task_ids.length} task{sprint.task_ids.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Actions */}
      <div
        className="flex gap-2 border-t border-border pt-2.5"
        onClick={(e) => e.stopPropagation()}
      >
        {sprint.status === "planned" && (
          <button
            disabled={start.isPending}
            onClick={() => start.mutate(sprint.id, {
              onSuccess: () => toast.success("Sprint started"),
              onError:   () => toast.error("Failed to start sprint"),
            })}
            className="h-6 rounded-[4px] border border-border bg-surface-3 px-2.5 font-mono text-[10px] text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
          >
            Start
          </button>
        )}
        {sprint.status === "active" && (
          <button
            disabled={complete.isPending}
            onClick={() => complete.mutate({ id: sprint.id, moveIncomplete: false }, {
              onSuccess: () => toast.success("Sprint completed"),
              onError:   () => toast.error("Failed to complete sprint"),
            })}
            className="h-6 rounded-[4px] border border-border bg-surface-3 px-2.5 font-mono text-[10px] text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
          >
            Complete
          </button>
        )}
        {sprint.status !== "active" && (
          <button
            disabled={del.isPending}
            onClick={() => del.mutate(sprint.id, {
              onSuccess: () => toast.success("Sprint deleted"),
              onError:   () => toast.error("Failed to delete sprint"),
            })}
            className="ml-auto h-6 rounded-[4px] px-2.5 font-mono text-[10px] text-destructive/70 transition-colors hover:text-destructive disabled:opacity-50"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  )
}
