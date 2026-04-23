import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useCreateGoal } from "@/api/hooks/goals"
import type { GoalCreate } from "@/api/hooks/goals"

interface Props {
  open: boolean
  onClose: () => void
}

const EMPTY: GoalCreate = { title: "", description: "", priority: "medium", tags: [] }

export function GoalCreateModal({ open, onClose }: Props) {
  const [form, setForm] = useState<GoalCreate>(EMPTY)
  const [error, setError] = useState<string | null>(null)
  const create = useCreateGoal()

  function handleClose() {
    setForm(EMPTY)
    setError(null)
    onClose()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.title.trim()) return setError("Title is required.")
    try {
      await create.mutateAsync(form)
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create goal.")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>New Goal</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="goal-title">Title *</Label>
            <Input
              id="goal-title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="e.g. Ship v1.0"
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="goal-priority">Priority</Label>
            <Select
              value={form.priority}
              onValueChange={(v) => setForm({ ...form, priority: v as GoalCreate["priority"] })}
            >
              <SelectTrigger id="goal-priority">
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
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>Cancel</Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Creating…" : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
