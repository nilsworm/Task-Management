import { useDroppable } from "@dnd-kit/core"
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable"
import { ScrollArea } from "@/components/ui/scroll-area"
import { KanbanTaskCard } from "./KanbanTaskCard"
import type { components } from "@/api/types"

type Task = components["schemas"]["TaskResponse"]

const COLUMN_META: Record<string, { label: string; color: string }> = {
  backlog:     { label: "Backlog",     color: "#5a5a7a" },
  todo:        { label: "To Do",       color: "#9090b0" },
  in_progress: { label: "In Progress", color: "#00d4ff" },
  review:      { label: "Review",      color: "#ffd166" },
  blocked:     { label: "Blocked",     color: "#ff4d6d" },
  done:        { label: "Done",        color: "#06d6a0" },
}

interface Props {
  status: string
  tasks: Task[]
}

export function KanbanColumn({ status, tasks }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: status })
  const { label, color } = COLUMN_META[status] ?? { label: status, color: "#5a5a7a" }

  return (
    <div
      data-testid={`column-${status}`}
      className={`flex w-[220px] shrink-0 flex-col gap-2 rounded-[6px] border bg-surface-2 transition-colors ${
        isOver ? "border-cyan/40 bg-surface-3" : "border-border"
      }`}
    >
      {/* Column header */}
      <div className="flex items-center gap-2 rounded-t-[5px] px-3 py-2.5 border-b border-border">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: color }} />
        <span className="flex-1 font-mono text-[11px] font-semibold" style={{ color }}>
          {label}
        </span>
        <span className="rounded bg-surface-3 px-1.5 font-mono text-[10px] font-bold text-muted-foreground">
          {tasks.length}
        </span>
      </div>

      <SortableContext items={tasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
        <ScrollArea>
          <div ref={setNodeRef} className="flex min-h-20 flex-col gap-1.5 p-2">
            {tasks.length === 0 && (
              <div className="rounded-[4px] border border-dashed border-border px-2 py-3 text-center">
                <span className="font-mono text-[9px] text-muted-foreground">empty</span>
              </div>
            )}
            {tasks.map((task) => (
              <KanbanTaskCard key={task.id} task={task} />
            ))}
          </div>
        </ScrollArea>
      </SortableContext>
    </div>
  )
}
