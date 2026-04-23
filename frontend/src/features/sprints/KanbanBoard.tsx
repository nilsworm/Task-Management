import { useState } from "react"
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter,
} from "@dnd-kit/core"
import type { DragStartEvent, DragEndEvent } from "@dnd-kit/core"
import { KanbanColumn } from "./KanbanColumn"
import { KanbanTaskCard } from "./KanbanTaskCard"
import { useTransitionTask } from "@/api/hooks/tasks"
import type { TaskStatus } from "@/api/hooks/tasks"
import type { components } from "@/api/types"

type Task = components["schemas"]["TaskResponse"]

const COLUMNS: TaskStatus[] = ["backlog", "todo", "in_progress", "review", "blocked", "done"]

interface Props {
  tasks: Task[]
}

export function KanbanBoard({ tasks }: Props) {
  const [activeId, setActiveId] = useState<string | null>(null)
  const transition = useTransitionTask()

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  )

  const activeTask = activeId ? tasks.find((t) => t.id === activeId) : null

  function tasksByStatus(status: string) {
    return tasks.filter((t) => t.status === status)
  }

  function handleDragStart(e: DragStartEvent) {
    setActiveId(String(e.active.id))
  }

  function handleDragEnd(e: DragEndEvent) {
    setActiveId(null)
    const { active, over } = e
    if (!over) return

    const taskId = String(active.id)
    const task = tasks.find((t) => t.id === taskId)
    if (!task) return

    // `over.id` is either a column status (droppable) or another task's id (sortable)
    const targetStatus = COLUMNS.includes(over.id as TaskStatus)
      ? (over.id as TaskStatus)
      : (tasks.find((t) => t.id === over.id)?.status as TaskStatus | undefined)

    if (!targetStatus || targetStatus === task.status) return

    transition.mutate({ id: taskId, status: targetStatus })
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 overflow-x-auto pb-4">
        {COLUMNS.map((status) => (
          <KanbanColumn key={status} status={status} tasks={tasksByStatus(status)} />
        ))}
      </div>

      <DragOverlay>
        {activeTask && <KanbanTaskCard task={activeTask} />}
      </DragOverlay>
    </DndContext>
  )
}
