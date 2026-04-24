import { useState } from "react"
import { TaskStatusBadge } from "./TaskStatusBadge"
import { TaskExpandedRow } from "./TaskExpandedRow"
import type { Task } from "@/api/hooks/tasks"

const PRIORITY_COLORS: Record<string, string> = {
  low:      "#9090b0",
  medium:   "#a78bfa",
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
  onDeleted?: () => void
}

export function TaskTable({ tasks, onDeleted }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  function toggleExpand(id: string) {
    setExpandedId((prev) => (prev === id ? null : id))
  }

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
      <div className="grid grid-cols-[24px_1fr_80px_110px_80px_52px] gap-3 border-b border-border bg-surface-1 px-3 py-2">
        {["", "Title", "Type", "Status", "Priority", "Pts"].map((h, i) => (
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
            {/* Collapsed row */}
            {!isExpanded && (
              <div
                onClick={() => toggleExpand(task.id)}
                className={`grid grid-cols-[24px_1fr_80px_110px_80px_52px] items-center gap-3 px-3 py-2 cursor-pointer transition-colors hover:bg-surface-3 ${
                  idx < tasks.length - 1 ? "border-b border-border" : ""
                }`}
              >
                {/* Quick-done checkbox */}
                <div
                  onClick={(e) => {
                    e.stopPropagation()
                    // handled by TaskExpandedRow transition — no-op here
                  }}
                  className={`flex h-4 w-4 items-center justify-center rounded-[3px] border transition-colors ${
                    isDone
                      ? "border-green bg-green/20"
                      : "border-border-strong bg-transparent"
                  }`}
                >
                  {isDone && (
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                      <path d="M2 5l2.5 2.5L8 3" stroke="#06d6a0" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </div>

                <span
                  className={`truncate text-xs font-medium ${isDone ? "text-muted-foreground line-through" : "text-foreground"}`}
                >
                  {task.title}
                </span>

                <span className="truncate font-mono text-[10px] text-muted-foreground">
                  {TYPE_LABELS[task.task_type] ?? task.task_type}
                </span>

                <div><TaskStatusBadge status={task.status} /></div>

                <div className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: priorityColor }} />
                  <span className="font-mono text-[10px]" style={{ color: priorityColor }}>
                    {task.priority}
                  </span>
                </div>

                <span className="font-mono text-[10px] text-muted-foreground">
                  {task.estimation != null ? `${task.estimation}pt` : "—"}
                </span>
              </div>
            )}

            {/* Expanded inline edit */}
            {isExpanded && (
              <TaskExpandedRow
                task={task}
                onClose={() => setExpandedId(null)}
                onDeleted={() => {
                  setExpandedId(null)
                  onDeleted?.()
                }}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
