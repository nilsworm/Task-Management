import { useDroppable } from "@dnd-kit/core"
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { KanbanTaskCard } from "./KanbanTaskCard"
import type { components } from "@/api/types"

type Task = components["schemas"]["TaskResponse"]

const COLUMN_COLORS: Record<string, string> = {
  backlog: "border-slate-200 dark:border-slate-700",
  todo: "border-blue-200 dark:border-blue-800",
  in_progress: "border-amber-200 dark:border-amber-800",
  review: "border-purple-200 dark:border-purple-800",
  blocked: "border-red-200 dark:border-red-800",
  done: "border-green-200 dark:border-green-800",
}

const HEADER_COLORS: Record<string, string> = {
  backlog: "bg-slate-50 dark:bg-slate-900",
  todo: "bg-blue-50 dark:bg-blue-950",
  in_progress: "bg-amber-50 dark:bg-amber-950",
  review: "bg-purple-50 dark:bg-purple-950",
  blocked: "bg-red-50 dark:bg-red-950",
  done: "bg-green-50 dark:bg-green-950",
}

const LABELS: Record<string, string> = {
  backlog: "Backlog",
  todo: "Todo",
  in_progress: "In Progress",
  review: "Review",
  blocked: "Blocked",
  done: "Done",
}

interface Props {
  status: string
  tasks: Task[]
}

export function KanbanColumn({ status, tasks }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: status })

  return (
    <div
      className={cn(
        "flex w-64 shrink-0 flex-col rounded-lg border-2",
        COLUMN_COLORS[status],
        isOver && "ring-2 ring-primary ring-offset-2",
      )}
    >
      <div className={cn("flex items-center justify-between rounded-t-md px-3 py-2", HEADER_COLORS[status])}>
        <span className="text-sm font-semibold">{LABELS[status]}</span>
        <span className="text-xs text-muted-foreground">{tasks.length}</span>
      </div>

      <SortableContext items={tasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
        <ScrollArea>
          <div ref={setNodeRef} className="flex min-h-24 flex-col gap-2 p-2">
            {tasks.map((task) => (
              <KanbanTaskCard key={task.id} task={task} />
            ))}
          </div>
        </ScrollArea>
      </SortableContext>
    </div>
  )
}
