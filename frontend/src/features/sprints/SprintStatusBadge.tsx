import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const LABELS: Record<string, string> = {
  planned: "Planned",
  active: "Active",
  completed: "Completed",
  cancelled: "Cancelled",
}

const CLASSES: Record<string, string> = {
  planned: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  active: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  completed: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  cancelled: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500",
}

export function SprintStatusBadge({ status }: { status: string }) {
  return (
    <Badge
      variant="outline"
      className={cn("border-transparent text-xs font-medium", CLASSES[status])}
    >
      {LABELS[status] ?? status}
    </Badge>
  )
}
