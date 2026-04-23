import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { useTasks } from "@/api/hooks/tasks"
import type { Task } from "@/api/hooks/tasks"
import { TaskFilterBar } from "./TaskFilterBar"
import { TaskTable } from "./TaskTable"
import { TaskCreateModal } from "./TaskCreateModal"
import { TaskEditModal } from "./TaskEditModal"
import { TaskDeleteDialog } from "./TaskDeleteDialog"
import type { TaskFilters } from "./TaskFilterBar"

const DEFAULT_FILTERS: TaskFilters = { status: "all", priority: "all", taskType: "all" }

export function TasksPage() {
  const [filters, setFilters] = useState<TaskFilters>(DEFAULT_FILTERS)
  const [createOpen, setCreateOpen] = useState(false)
  const [editTask, setEditTask] = useState<Task | null>(null)
  const [deleteTask, setDeleteTask] = useState<Task | null>(null)

  const { data: tasks = [], isLoading, isError } = useTasks()

  const visible = tasks.filter((t) => {
    if (filters.status !== "all" && t.status !== filters.status) return false
    if (filters.priority !== "all" && t.priority !== filters.priority) return false
    if (filters.taskType !== "all" && t.task_type !== filters.taskType) return false
    return true
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Tasks</h1>
          <p className="text-sm text-muted-foreground">
            {isLoading ? "Loading…" : `${visible.length} of ${tasks.length} tasks`}
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Task
        </Button>
      </div>

      <TaskFilterBar filters={filters} onChange={setFilters} />

      {isError && (
        <p className="text-sm text-destructive">Failed to load tasks. Is the backend running?</p>
      )}

      {!isLoading && !isError && (
        <TaskTable tasks={visible} onEdit={setEditTask} onDelete={setDeleteTask} />
      )}

      <TaskCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
      <TaskEditModal task={editTask} onClose={() => setEditTask(null)} />
      <TaskDeleteDialog task={deleteTask} onClose={() => setDeleteTask(null)} />
    </div>
  )
}
