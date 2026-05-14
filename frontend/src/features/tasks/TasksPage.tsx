import { useState } from "react"
import { LayoutList, LayoutGrid, Plus } from "lucide-react"
import { useTasks } from "@/api/hooks/tasks"
import { useDebounce } from "@/lib/useDebounce"
import { TaskFilterBar } from "./TaskFilterBar"
import { TaskTable } from "./TaskTable"
import { TaskBoardView } from "./TaskBoardView"
import { TaskCreateModal } from "./TaskCreateModal"
import type { TaskFilters } from "./TaskFilterBar"

type ViewMode = "list" | "board"

const DEFAULT_FILTERS: TaskFilters = { search: "", status: "all", priority: "all", taskType: "all" }

function RowSkeleton() {
  return <div className="h-9 animate-pulse rounded-[5px] bg-surface-3" />
}

export function TasksPage() {
  const [view, setView]           = useState<ViewMode>("list")
  const [filters, setFilters]     = useState<TaskFilters>(DEFAULT_FILTERS)
  const [createOpen, setCreateOpen] = useState(false)

  const debouncedSearch = useDebounce(filters.search, 300)

  const { data: tasks = [], isLoading, isError } = useTasks(
    debouncedSearch ? { search: debouncedSearch } : {}
  )

  const visible = tasks.filter((t) => {
    if (filters.status !== "all" && t.status !== filters.status) return false
    if (filters.priority !== "all" && t.priority !== filters.priority) return false
    if (filters.taskType !== "all" && t.task_type !== filters.taskType) return false
    return true
  })

  return (
    <div className="flex flex-col gap-3">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-semibold text-foreground">Tasks</h1>
          <span className="font-mono text-[11px] text-muted-foreground">
            {isLoading ? "…" : `${visible.length} / ${tasks.length}`}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex items-center rounded-[5px] border border-border bg-surface-2 p-0.5">
            <button
              onClick={() => setView("list")}
              className={`flex h-6 w-6 items-center justify-center rounded-[4px] transition-colors ${
                view === "list"
                  ? "bg-surface-3 text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              aria-label="List view"
            >
              <LayoutList className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => setView("board")}
              className={`flex h-6 w-6 items-center justify-center rounded-[4px] transition-colors ${
                view === "board"
                  ? "bg-surface-3 text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              aria-label="Board view"
            >
              <LayoutGrid className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* New task button */}
          <button
            onClick={() => setCreateOpen(true)}
            className="flex h-7 items-center gap-1.5 rounded-[5px] border border-border bg-surface-2 px-3 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
          >
            <Plus className="h-3 w-3" />
            New task
          </button>
        </div>
      </div>

      {/* Filters */}
      <TaskFilterBar filters={filters} onChange={setFilters} />

      {/* Error state */}
      {isError && (
        <p className="text-[11px] text-destructive">
          Failed to load tasks. Is the backend running?
        </p>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex flex-col gap-1.5">
          {[...Array(6)].map((_, i) => <RowSkeleton key={i} />)}
        </div>
      )}

      {/* Content */}
      {!isLoading && !isError && view === "list" && (
        <TaskTable tasks={visible} />
      )}
      {!isLoading && !isError && view === "board" && (
        <TaskBoardView tasks={visible} />
      )}

      <TaskCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  )
}
