import { MoreHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useTransitionTask } from "@/api/hooks/tasks"
import { TRANSITIONS } from "./taskTransitions"
import type { Task, TaskStatus } from "@/api/hooks/tasks"

const STATUS_LABELS: Record<TaskStatus, string> = {
  backlog: "Backlog",
  todo: "Todo",
  in_progress: "In Progress",
  review: "Review",
  blocked: "Blocked",
  done: "Done",
  cancelled: "Cancelled",
}

interface Props {
  task: Task
  onEdit: () => void
  onDelete: () => void
}

export function TaskActions({ task, onEdit, onDelete }: Props) {
  const transition = useTransitionTask()
  const nextStatuses = TRANSITIONS[task.status as TaskStatus] ?? []

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-7 w-7">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {nextStatuses.length > 0 && (
          <>
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Move to
            </DropdownMenuLabel>
            {nextStatuses.map((s) => (
              <DropdownMenuItem
                key={s}
                onClick={() => transition.mutate({ id: task.id, status: s })}
              >
                {STATUS_LABELS[s]}
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
          </>
        )}
        <DropdownMenuItem onClick={onEdit}>Edit</DropdownMenuItem>
        <DropdownMenuItem
          onClick={onDelete}
          className="text-destructive focus:text-destructive"
        >
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
