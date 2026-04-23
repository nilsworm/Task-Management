import { useEffect, useState } from "react"
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
import { useUpdateKeyResult } from "@/api/hooks/goals"
import type { KeyResult } from "@/api/hooks/goals"

interface Props {
  goalId: string
  kr: KeyResult | null
  onClose: () => void
}

export function KeyResultEditModal({ goalId, kr, onClose }: Props) {
  const [current, setCurrent] = useState("")
  const [error, setError] = useState<string | null>(null)
  const update = useUpdateKeyResult(goalId)

  useEffect(() => {
    if (kr) {
      setCurrent(String(kr.current_value))
      setError(null)
    }
  }, [kr])

  if (!kr) return null

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const val = Number(current)
    if (isNaN(val) || val < 0) return setError("Must be a non-negative number.")
    try {
      await update.mutateAsync({ id: kr!.id, current_value: val })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update.")
    }
  }

  return (
    <Dialog open={!!kr} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Update Progress</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">{kr.title}</p>
          <div className="grid gap-1.5">
            <Label htmlFor="kr-edit-current">
              Current value{kr.unit ? ` (${kr.unit})` : ""}
            </Label>
            <Input
              id="kr-edit-current"
              type="number"
              min={0}
              step="any"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              autoFocus
            />
            <p className="text-xs text-muted-foreground">
              Target: {kr.target_value}{kr.unit ? ` ${kr.unit}` : ""}
            </p>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={update.isPending}>
              {update.isPending ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
