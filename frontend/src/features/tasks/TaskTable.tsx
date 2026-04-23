import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { TaskStatusBadge } from "./TaskStatusBadge"
import { TaskActions } from "./TaskActions"
import type { Task } from "@/api/hooks/tasks"

const PRIORITY_CLASSES: Record<string, string> = {
  low: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
  medium: "bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400",
  high: "bg-orange-100 text-orange-600 dark:bg-orange-900 dark:text-orange-400",
  critical: "bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400",
}

interface Props {
  tasks: Task[]
  onEdit: (task: Task) => void
  onDelete: (task: Task) => void
}

export function TaskTable({ tasks, onEdit, onDelete }: Props) {
  if (tasks.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-muted-foreground">
        No tasks found. Create one to get started.
      </p>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Title</TableHead>
          <TableHead className="w-28">Type</TableHead>
          <TableHead className="w-32">Status</TableHead>
          <TableHead className="w-24">Priority</TableHead>
          <TableHead className="w-20">Points</TableHead>
          <TableHead className="w-10" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {tasks.map((task) => (
          <TableRow key={task.id}>
            <TableCell className="font-medium">{task.title}</TableCell>
            <TableCell>
              <span className="text-xs text-muted-foreground">{task.task_type}</span>
            </TableCell>
            <TableCell>
              <TaskStatusBadge status={task.status} />
            </TableCell>
            <TableCell>
              <Badge
                variant="outline"
                className={`border-transparent text-xs ${PRIORITY_CLASSES[task.priority] ?? ""}`}
              >
                {task.priority}
              </Badge>
            </TableCell>
            <TableCell className="text-sm text-muted-foreground">
              {task.estimation ?? "—"}
            </TableCell>
            <TableCell>
              <TaskActions
                task={task}
                onEdit={() => onEdit(task)}
                onDelete={() => onDelete(task)}
              />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
