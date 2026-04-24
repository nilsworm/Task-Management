import { useState } from "react"
import { X } from "lucide-react"
import { useRemoveTaskFromSprint } from "@/api/hooks/sprints"
import { TaskExpandedRow } from "@/features/tasks/TaskExpandedRow"
import { TaskStatusBadge } from "@/features/tasks/TaskStatusBadge"
import type { components } from "@/api/types"
import { toast } from "sonner"

type Task = components["schemas"]["TaskResponse"]

const PRIORITY_COLORS: Record<string, string> = {
  low:      "#9090b0",
  medium:   "#a78bfa",
  high:     "#ffd166",
  critical: "#ff4d6d",
}

interface Props {
  tasks: Task[]
  sprintId: string
}

export function SprintTaskList({ tasks, sprintId }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const remove = useRemoveTaskFromSprint(sprintId)

  if (tasks.length === 0) {
    return (
      <p className="py-12 text-center text-[11px] text-muted-foreground">
        No tasks in this sprint yet.
      </p>
    )
  }

  return (
    <div className="flex flex-col rounded-[6px] border border-border bg-surface-2 overflow-hidden">
      <div className="grid grid-cols-[1fr_110px_80px_52px_28px] gap-3 border-b border-border bg-surface-1 px-3 py-2">
        {["Title", "Status", "Priority", "Pts", ""].map((h, i) => (
          <span key={i} className="font-mono text-[10px] font-semibold uppercase tracking-[0.5px] text-muted-foreground">
            {h}
          </span>
        ))}
      </div>

      {tasks.map((task, idx) => {
        const isExpanded = expandedId === task.id
        const priorityColor = PRIORITY_COLORS[task.priority] ?? "#9090b0"
        const isDone = task.status === "done"

        return (
          <div key={task.id}>
            {!isExpanded && (
              <div
                onClick={() => setExpandedId(task.id)}
                className={`grid grid-cols-[1fr_110px_80px_52px_28px] items-center gap-3 px-3 py-2 cursor-pointer transition-colors hover:bg-surface-3 ${
                  idx < tasks.length - 1 ? "border-b border-border" : ""
                }`}
              >
                <span className={`truncate text-xs font-medium ${isDone ? "text-muted-foreground line-through" : "text-foreground"}`}>
                  {task.title}
                </span>
                <div><TaskStatusBadge status={task.status} /></div>
                <div className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: priorityColor }} />
                  <span className="font-mono text-[10px]" style={{ color: priorityColor }}>{task.priority}</span>
                </div>
                <span className="font-mono text-[10px] text-muted-foreground">
                  {task.estimation != null ? `${task.estimation}pt` : "—"}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    remove.mutate(task.id, {
                      onSuccess: () => toast.success("Task removed from sprint"),
                      onError: () => toast.error("Failed to remove task"),
                    })
                  }}
                  className="flex h-5 w-5 items-center justify-center rounded-[3px] text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                  aria-label="Remove from sprint"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            )}

            {isExpanded && (
              <TaskExpandedRow
                task={task}
                onClose={() => setExpandedId(null)}
                onDeleted={() => setExpandedId(null)}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
