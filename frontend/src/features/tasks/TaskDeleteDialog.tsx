import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { useDeleteTask } from "@/api/hooks/tasks"
import type { Task } from "@/api/hooks/tasks"
import { toast } from "sonner"

interface Props {
  task: Task | null
  onClose: () => void
}

export function TaskDeleteDialog({ task, onClose }: Props) {
  const del = useDeleteTask()

  async function handleConfirm() {
    if (!task) return
    try {
      await del.mutateAsync(task.id)
      toast.success("Task deleted")
      onClose()
    } catch {
      toast.error("Failed to delete task")
    }
  }

  return (
    <AlertDialog open={!!task} onOpenChange={(o) => !o && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete task?</AlertDialogTitle>
          <AlertDialogDescription>
            &ldquo;{task?.title}&rdquo; will be permanently deleted. This cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            disabled={del.isPending}
          >
            {del.isPending ? "Deleting…" : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
