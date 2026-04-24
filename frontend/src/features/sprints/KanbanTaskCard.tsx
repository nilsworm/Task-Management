import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { cn } from "@/lib/utils"
import type { components } from "@/api/types"

type Task = components["schemas"]["TaskResponse"]

const PRIORITY_COLORS: Record<string, string> = {
  low:      "#5a5a7a",
  medium:   "#9090b0",
  high:     "#ffd166",
  critical: "#ff4d6d",
}

interface Props { task: Task }

export function KanbanTaskCard({ task }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: task.id })

  const style = { transform: CSS.Transform.toString(transform), transition }
  const priorityColor = PRIORITY_COLORS[task.priority] ?? "#5a5a7a"

  return (
    <div
      ref={setNodeRef}
      style={style}
      data-testid={`task-card-${task.id}`}
      {...attributes}
      {...listeners}
      className={cn(
        "flex cursor-grab select-none flex-col gap-2 rounded-[5px] border border-border bg-surface-3 p-2.5 transition-colors active:cursor-grabbing hover:bg-surface-4",
        isDragging && "opacity-50 shadow-lg",
      )}
    >
      <p className="text-[11px] font-medium leading-snug text-foreground line-clamp-2">{task.title}</p>

      <div className="flex items-center gap-1.5">
        <span
          className="h-1.5 w-1.5 rounded-full"
          style={{ background: priorityColor }}
          title={task.priority}
        />
        <span className="font-mono text-[9px]" style={{ color: priorityColor }}>
          {task.priority}
        </span>
        {task.estimation != null && (
          <>
            <span className="text-[9px] text-muted-foreground">·</span>
            <span className="rounded bg-surface-2 px-1 font-mono text-[9px] text-muted-foreground">
              {task.estimation}pt
            </span>
          </>
        )}
      </div>
    </div>
  )
}
