import { useState } from "react"
import { Plus } from "lucide-react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useTasks } from "@/api/hooks/tasks"
import { useAddTaskToSprint } from "@/api/hooks/sprints"
import { toast } from "sonner"

interface Props {
  sprintId: string
  assignedTaskIds: string[]
}

export function SprintAssignTask({ sprintId, assignedTaskIds }: Props) {
  const [selectedId, setSelectedId] = useState("")
  const { data: allTasks = [] } = useTasks()
  const assign = useAddTaskToSprint(sprintId)

  const assignable = allTasks.filter(
    (t) => t.task_type === "sprint" && !assignedTaskIds.includes(t.id),
  )

  if (assignable.length === 0) return null

  function handleAssign() {
    if (!selectedId) return
    assign.mutate(selectedId, {
      onSuccess: () => {
        toast.success("Task assigned to sprint")
        setSelectedId("")
      },
      onError: () => toast.error("Failed to assign task"),
    })
  }

  return (
    <div className="flex items-center gap-2">
      <Select value={selectedId} onValueChange={setSelectedId}>
        <SelectTrigger className="h-7 w-52 rounded-[5px] border-border bg-surface-2 font-mono text-[11px] text-muted-foreground">
          <SelectValue placeholder="Assign existing task…" />
        </SelectTrigger>
        <SelectContent className="font-mono text-[11px]">
          {assignable.map((t) => (
            <SelectItem key={t.id} value={t.id} className="text-[11px]">
              {t.title}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <button
        disabled={!selectedId || assign.isPending}
        onClick={handleAssign}
        className="flex h-7 w-7 items-center justify-center rounded-[5px] border border-border bg-surface-2 text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground disabled:opacity-40"
        aria-label="Assign task"
      >
        <Plus className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}
