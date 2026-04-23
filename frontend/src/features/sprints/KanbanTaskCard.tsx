import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { components } from "@/api/types"

type Task = components["schemas"]["TaskResponse"]

const PRIORITY_DOT: Record<string, string> = {
  low: "bg-slate-400",
  medium: "bg-blue-400",
  high: "bg-orange-400",
  critical: "bg-red-500",
}

interface Props {
  task: Task
}

export function KanbanTaskCard({ task }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: task.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <Card
        className={cn(
          "cursor-grab select-none active:cursor-grabbing",
          isDragging && "opacity-50 shadow-lg",
        )}
      >
        <CardContent className="p-3">
          <p className="text-sm font-medium leading-snug">{task.title}</p>
          <div className="mt-2 flex items-center gap-2">
            <span
              className={cn("h-2 w-2 rounded-full", PRIORITY_DOT[task.priority] ?? "bg-gray-400")}
              title={task.priority}
            />
            {task.estimation !== null && (
              <Badge variant="outline" className="h-4 px-1 text-xs">
                {task.estimation}p
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
