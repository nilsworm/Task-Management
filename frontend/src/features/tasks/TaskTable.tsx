import { TaskStatusBadge } from "./TaskStatusBadge"
import { TaskActions } from "./TaskActions"
import type { Task } from "@/api/hooks/tasks"

const PRIORITY_COLORS: Record<string, string> = {
  low:      "#5a5a7a",
  medium:   "#9090b0",
  high:     "#ffd166",
  critical: "#ff4d6d",
}

const TYPE_LABELS: Record<string, string> = {
  daily:     "daily",
  sprint:    "sprint",
  goal:      "goal",
  milestone: "milestone",
}

interface Props {
  tasks: Task[]
  onEdit: (task: Task) => void
  onDelete: (task: Task) => void
}

export function TaskTable({ tasks, onEdit, onDelete }: Props) {
  if (tasks.length === 0) {
    return (
      <p className="py-12 text-center text-[11px] text-muted-foreground">
        No tasks match the current filters.
      </p>
    )
  }

  return (
    <div className="flex flex-col rounded-[6px] border border-border bg-surface-2 overflow-hidden">
      {/* Column headers */}
      <div className="grid grid-cols-[1fr_80px_110px_80px_52px_36px] gap-3 border-b border-border px-3 py-2">
        {["Title", "Type", "Status", "Priority", "Pts", ""].map((h, i) => (
          <span key={i} className="font-mono text-[10px] font-semibold uppercase tracking-[0.5px] text-muted-foreground">
            {h}
          </span>
        ))}
      </div>

      {tasks.map((task, idx) => {
        const priorityColor = PRIORITY_COLORS[task.priority] ?? "#5a5a7a"
        return (
          <div
            key={task.id}
            className={`grid grid-cols-[1fr_80px_110px_80px_52px_36px] items-center gap-3 px-3 py-2 transition-colors hover:bg-surface-3 ${
              idx < tasks.length - 1 ? "border-b border-border" : ""
            }`}
          >
            <span className="truncate text-xs font-medium text-foreground">{task.title}</span>

            <span className="truncate font-mono text-[10px] text-muted-foreground">
              {TYPE_LABELS[task.task_type] ?? task.task_type}
            </span>

            <div>
              <TaskStatusBadge status={task.status} />
            </div>

            <div className="flex items-center gap-1.5">
              <span
                className="h-1.5 w-1.5 shrink-0 rounded-full"
                style={{ background: priorityColor }}
              />
              <span className="font-mono text-[10px]" style={{ color: priorityColor }}>
                {task.priority}
              </span>
            </div>

            <span className="font-mono text-[10px] text-muted-foreground">
              {task.estimation != null ? `${task.estimation}pt` : "—"}
            </span>

            <div className="flex justify-end">
              <TaskActions task={task} onEdit={() => onEdit(task)} onDelete={() => onDelete(task)} />
            </div>
          </div>
        )
      })}
    </div>
  )
}
