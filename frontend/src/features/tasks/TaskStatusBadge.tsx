import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { TaskStatus } from "@/api/hooks/tasks"

const STATUS_LABELS: Record<TaskStatus, string> = {
  backlog: "Backlog",
  todo: "Todo",
  in_progress: "In Progress",
  review: "Review",
  blocked: "Blocked",
  done: "Done",
  cancelled: "Cancelled",
}

const STATUS_CLASSES: Record<TaskStatus, string> = {
  backlog: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  todo: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  in_progress: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  review: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  blocked: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  done: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  cancelled: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500",
}

interface Props {
  status: string
}

export function TaskStatusBadge({ status }: Props) {
  const s = status as TaskStatus
  return (
    <Badge
      variant="outline"
      className={cn("border-transparent text-xs font-medium", STATUS_CLASSES[s])}
    >
      {STATUS_LABELS[s] ?? status}
    </Badge>
  )
}
