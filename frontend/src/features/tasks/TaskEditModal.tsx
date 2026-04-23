import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useUpdateTask } from "@/api/hooks/tasks"
import type { Task, TaskUpdate } from "@/api/hooks/tasks"

interface Props {
  task: Task | null
  onClose: () => void
}

export function TaskEditModal({ task, onClose }: Props) {
  const [form, setForm] = useState<Omit<TaskUpdate, "id">>({})
  const [error, setError] = useState<string | null>(null)
  const update = useUpdateTask()

  useEffect(() => {
    if (task) {
      setForm({
        title: task.title,
        description: task.description,
        priority: task.priority as TaskUpdate["priority"],
        estimation: task.estimation,
      })
      setError(null)
    }
  }, [task])

  if (!task) return null

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.title?.trim()) {
      setError("Title is required.")
      return
    }
    try {
      await update.mutateAsync({ id: task!.id, ...form })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task.")
    }
  }

  return (
    <Dialog open={!!task} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit Task</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="edit-title">Title *</Label>
            <Input
              id="edit-title"
              value={form.title ?? ""}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="edit-description">Description</Label>
            <Textarea
              id="edit-description"
              rows={3}
              value={form.description ?? ""}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="edit-priority">Priority</Label>
            <Select
              value={form.priority ?? "medium"}
              onValueChange={(v) =>
                setForm({ ...form, priority: v as TaskUpdate["priority"] })
              }
            >
              <SelectTrigger id="edit-priority">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="edit-estimation">Story Points</Label>
            <Input
              id="edit-estimation"
              type="number"
              min={1}
              max={100}
              placeholder="1–100 (optional)"
              value={form.estimation ?? ""}
              onChange={(e) =>
                setForm({
                  ...form,
                  estimation: e.target.value ? Number(e.target.value) : null,
                })
              }
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={update.isPending}>
              {update.isPending ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
