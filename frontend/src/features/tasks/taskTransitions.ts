import type { TaskStatus } from "@/api/hooks/tasks"

export const TRANSITIONS: Record<TaskStatus, TaskStatus[]> = {
  backlog: ["todo", "cancelled"],
  todo: ["in_progress", "backlog", "cancelled"],
  in_progress: ["review", "blocked", "todo", "cancelled"],
  review: ["done", "in_progress", "cancelled"],
  blocked: ["in_progress", "cancelled"],
  done: [],
  cancelled: [],
}
