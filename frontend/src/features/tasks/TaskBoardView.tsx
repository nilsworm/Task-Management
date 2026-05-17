import { useTransitionTask } from "@/api/hooks/tasks"
import { TRANSITIONS } from "./taskTransitions"
import type { Task, TaskStatus } from "@/api/hooks/tasks"

function isTaskOverdue(task: Task): boolean {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  if (!task.due_date) return false
  const due = new Date(task.due_date)
  return due < today && !["done", "cancelled"].includes(task.status)
}

const COLUMNS: { key: string; label: string; color: string }[] = [
  { key: "backlog",     label: "Backlog",     color: "#5a5a7a" },
  { key: "todo",        label: "To Do",       color: "#9090b0" },
  { key: "in_progress", label: "In Progress", color: "#00d4ff" },
  { key: "review",      label: "Review",      color: "#ffd166" },
  { key: "blocked",     label: "Blocked",     color: "#ff4d6d" },
  { key: "done",        label: "Done",        color: "#06d6a0" },
]

const NEXT_LABEL: Record<TaskStatus, string> = {
  backlog:     "→ To Do",
  todo:        "→ In Progress",
  in_progress: "→ Review",
  review:      "→ Done",
  blocked:     "→ To Do",
  done:        "",
  cancelled:   "",
}

const PRIORITY_COLORS: Record<string, string> = {
  low:      "#5a5a7a",
  medium:   "#9090b0",
  high:     "#ffd166",
  critical: "#ff4d6d",
}

interface Props {
  tasks: Task[]
}

function BoardCard({ task }: { task: Task }) {
  const transition = useTransitionTask()
  const nextStatuses = TRANSITIONS[task.status as TaskStatus] ?? []
  const primaryNext = nextStatuses[0] as TaskStatus | undefined
  const priorityColor = PRIORITY_COLORS[task.priority] ?? "#5a5a7a"
  const overdue = isTaskOverdue(task)

  return (
    <div
      className="flex flex-col gap-2 rounded-[5px] border border-border bg-surface-2 p-3 transition-colors hover:bg-surface-3"
      style={{ borderLeft: `2px solid ${overdue ? "#ff4d6d" : priorityColor}` }}
    >
      <span className={`text-xs font-medium leading-snug line-clamp-2 ${overdue ? "text-red" : "text-foreground"}`}>
        {task.title}
      </span>

      <div className="flex items-center justify-between gap-1">
        <div className="flex items-center gap-1">
          <span className="font-mono text-[9px] text-muted-foreground">{task.task_type}</span>
          {task.estimation != null && (
            <>
              <span className="text-[9px] text-muted-foreground">·</span>
              <span className="rounded bg-surface-3 px-1 font-mono text-[9px] font-semibold text-muted-foreground">
                {task.estimation}pt
              </span>
            </>
          )}
        </div>

        {primaryNext && (
          <button
            onClick={() => transition.mutate({ id: task.id, status: primaryNext })}
            disabled={transition.isPending}
            className="rounded-[3px] border border-border px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground transition-colors hover:border-cyan/40 hover:text-cyan disabled:opacity-50"
          >
            {NEXT_LABEL[task.status as TaskStatus] || `→ ${primaryNext}`}
          </button>
        )}
      </div>
    </div>
  )
}

export function TaskBoardView({ tasks }: Props) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {COLUMNS.map(({ key, label, color }) => {
        const col = tasks.filter((t) => t.status === key)
        return (
          <div key={key} className="flex w-[220px] shrink-0 flex-col gap-2">
            <div className="flex items-center gap-2 rounded-[5px] border border-border bg-surface-2 px-3 py-2">
              <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: color }} />
              <span className="flex-1 font-mono text-[11px] font-semibold" style={{ color }}>
                {label}
              </span>
              <span className="rounded bg-surface-3 px-1.5 font-mono text-[10px] font-bold text-muted-foreground">
                {col.length}
              </span>
            </div>

            <div className="flex flex-col gap-2">
              {col.length === 0 ? (
                <div className="rounded-[5px] border border-dashed border-border px-3 py-4 text-center">
                  <span className="font-mono text-[10px] text-muted-foreground">empty</span>
                </div>
              ) : (
                col.map((task) => <BoardCard key={task.id} task={task} />)
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
