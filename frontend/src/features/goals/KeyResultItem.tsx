import { Pencil, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useDeleteKeyResult } from "@/api/hooks/goals"
import type { KeyResult } from "@/api/hooks/goals"

interface Props {
  kr: KeyResult
  onEdit: (kr: KeyResult) => void
}

export function KeyResultItem({ kr, onEdit }: Props) {
  const del = useDeleteKeyResult(kr.goal_id)
  const pct = Math.min(Math.max(kr.progress_percent, 0), 100)

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <p className="text-sm font-medium">{kr.title}</p>
          {kr.description && (
            <p className="text-xs text-muted-foreground">{kr.description}</p>
          )}
        </div>
        <div className="flex gap-1 shrink-0">
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onEdit(kr)}>
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-destructive hover:text-destructive"
            disabled={del.isPending}
            onClick={() => del.mutate(kr.id)}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex-1">
          <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${pct}%` }}
              role="progressbar"
              aria-valuenow={pct}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </div>
        <span className="w-28 text-right text-xs text-muted-foreground shrink-0">
          {kr.current_value} / {kr.target_value}{kr.unit ? ` ${kr.unit}` : ""} ({pct.toFixed(0)}%)
        </span>
      </div>
    </div>
  )
}
