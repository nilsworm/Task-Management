import { useState } from "react"
import { Search, X } from "lucide-react"
import { useTasks } from "@/api/hooks/tasks"
import { useAddTaskToSprint } from "@/api/hooks/sprints"
import { TaskStatusBadge } from "@/features/tasks/TaskStatusBadge"
import { toast } from "sonner"

interface Props {
  sprintId: string
  assignedTaskIds: string[]
  onClose: () => void
}

const PRIORITY_COLORS: Record<string, string> = {
  low:      "#9090b0",
  medium:   "#a78bfa",
  high:     "#ffd166",
  critical: "#ff4d6d",
}

export function SprintTaskPicker({ sprintId, assignedTaskIds, onClose }: Props) {
  const [query, setQuery] = useState("")
  const { data: allTasks = [] } = useTasks()
  const assign = useAddTaskToSprint(sprintId)

  const available = allTasks.filter(
    (t) => !assignedTaskIds.includes(t.id) && t.status !== "done" && t.status !== "cancelled",
  )

  const filtered = query
    ? available.filter((t) => t.title.toLowerCase().includes(query.toLowerCase()))
    : available

  function handleAssign(taskId: string) {
    assign.mutate(taskId, {
      onSuccess: () => toast.success("Task assigned to sprint"),
      onError: () => toast.error("Failed to assign task"),
    })
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="flex w-[480px] max-h-[70vh] flex-col rounded-[8px] border border-border bg-surface-1 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
          <span className="font-mono text-[11px] font-semibold text-foreground">Assign Existing Task</span>
          <button
            onClick={onClose}
            className="flex h-6 w-6 items-center justify-center rounded-[4px] text-muted-foreground transition-colors hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Search */}
        <div className="border-b border-border px-3 py-2.5">
          <div className="flex items-center gap-2 rounded-[5px] border border-border bg-surface-2 px-2.5">
            <Search className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search tasks…"
              className="flex-1 bg-transparent py-1.5 font-mono text-[11px] text-foreground outline-none placeholder:text-muted-foreground/50"
            />
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {filtered.length === 0 ? (
            <p className="py-10 text-center font-mono text-[11px] text-muted-foreground">
              {available.length === 0 ? "No unassigned tasks available." : "No results."}
            </p>
          ) : (
            filtered.map((task) => {
              const priorityColor = PRIORITY_COLORS[task.priority] ?? "#9090b0"
              return (
                <div
                  key={task.id}
                  onClick={() => handleAssign(task.id)}
                  className="flex cursor-pointer items-center gap-3 border-b border-border px-4 py-2.5 transition-colors last:border-b-0 hover:bg-surface-2"
                >
                  <span className="flex-1 truncate text-[11px] text-foreground">{task.title}</span>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className="h-1.5 w-1.5 rounded-full" style={{ background: priorityColor }} />
                    <span className="font-mono text-[10px]" style={{ color: priorityColor }}>{task.priority}</span>
                  </div>
                  <TaskStatusBadge status={task.status} />
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
