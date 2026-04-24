import type { TaskStatus } from "@/api/hooks/tasks"

const STATUS_LABELS: Record<TaskStatus, string> = {
  backlog:     "Backlog",
  todo:        "To Do",
  in_progress: "In Progress",
  review:      "Review",
  blocked:     "Blocked",
  done:        "Done",
  cancelled:   "Cancelled",
}

const STATUS_COLORS: Record<TaskStatus, string> = {
  backlog:     "#5a5a7a",
  todo:        "#9090b0",
  in_progress: "#00d4ff",
  review:      "#ffd166",
  blocked:     "#ff4d6d",
  done:        "#06d6a0",
  cancelled:   "#333350",
}

interface Props { status: string }

export function TaskStatusBadge({ status }: Props) {
  const s = status as TaskStatus
  const color = STATUS_COLORS[s] ?? "#5a5a7a"
  return (
    <span
      className="inline-flex items-center rounded-[3px] px-1.5 py-0.5 font-mono text-[10px] font-semibold"
      style={{ background: `${color}22`, color }}
    >
      {STATUS_LABELS[s] ?? status}
    </span>
  )
}
