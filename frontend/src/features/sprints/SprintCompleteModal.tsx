import { useState } from "react"
import { AlertCircle, CheckCircle2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import type { Sprint } from "@/api/hooks/sprints"

interface Props {
  sprint: Sprint
  isOpen: boolean
  doneCount: number
  totalCount: number
  onClose: () => void
  onConfirm: (moveIncomplete: boolean) => void
  isPending: boolean
}

export function SprintCompleteModal({
  sprint,
  isOpen,
  doneCount,
  totalCount,
  onClose,
  onConfirm,
  isPending,
}: Props) {
  const [moveIncomplete, setMoveIncomplete] = useState(false)
  const incompleteCount = totalCount - doneCount
  const velocity = doneCount

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="w-[400px]">
        <DialogHeader>
          <DialogTitle>Complete Sprint</DialogTitle>
          <DialogDescription>Review and confirm sprint completion</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Sprint summary */}
          <div className="rounded-[5px] border border-border bg-surface-2 p-3">
            <div className="mb-3 font-mono text-[11px] font-semibold uppercase text-muted-foreground">
              {sprint.name}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-[10px] text-muted-foreground">Completed</div>
                <div className="flex items-center gap-1.5 text-sm font-semibold text-green">
                  <CheckCircle2 className="h-4 w-4" />
                  {doneCount} / {totalCount}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-muted-foreground">Velocity</div>
                <div className="font-mono text-sm font-bold text-foreground">
                  {velocity}
                  <span className="ml-1 text-[10px] font-normal text-muted-foreground">pts</span>
                </div>
              </div>
            </div>
          </div>

          {/* Move incomplete option */}
          {incompleteCount > 0 && (
            <div className="rounded-[5px] border border-border bg-surface-2 p-3">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={moveIncomplete}
                  onChange={(e) => setMoveIncomplete(e.target.checked)}
                  disabled={isPending}
                  className="h-4 w-4 rounded-[3px] border border-border bg-surface-3"
                />
                <span className="text-xs font-medium text-foreground">
                  Move {incompleteCount} incomplete {incompleteCount === 1 ? "task" : "tasks"} to backlog
                </span>
              </label>
              <p className="mt-2 text-[10px] text-muted-foreground">
                Without this, incomplete tasks remain assigned to the sprint.
              </p>
            </div>
          )}

          {/* Warning if not moving incomplete */}
          {incompleteCount > 0 && !moveIncomplete && (
            <div className="flex gap-2 rounded-[5px] border border-yellow/30 bg-yellow/5 p-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0 text-yellow" />
              <p className="text-[10px] text-muted-foreground">
                {incompleteCount} incomplete {incompleteCount === 1 ? "task" : "tasks"} will remain in this sprint.
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <button
            onClick={onClose}
            disabled={isPending}
            className="rounded-[5px] border border-border bg-surface-2 px-3 py-2 text-[11px] font-medium text-foreground transition-colors hover:bg-surface-3 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(moveIncomplete)}
            disabled={isPending}
            className="rounded-[5px] border border-green/30 bg-green/10 px-3 py-2 text-[11px] font-medium text-green transition-colors hover:bg-green/20 disabled:opacity-50"
          >
            {isPending ? "Completing…" : "Complete Sprint"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
