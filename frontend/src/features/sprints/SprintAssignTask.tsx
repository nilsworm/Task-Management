import { useState } from "react"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
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
        <SelectTrigger className="w-56 h-8 text-xs">
          <SelectValue placeholder="Assign existing task…" />
        </SelectTrigger>
        <SelectContent>
          {assignable.map((t) => (
            <SelectItem key={t.id} value={t.id} className="text-xs">
              {t.title}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        size="sm"
        variant="outline"
        className="h-8"
        disabled={!selectedId || assign.isPending}
        onClick={handleAssign}
      >
        <Plus className="h-3.5 w-3.5" />
      </Button>
    </div>
  )
}
