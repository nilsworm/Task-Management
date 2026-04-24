import { Pencil, Trash2 } from "lucide-react"
import { useDeleteKeyResult } from "@/api/hooks/goals"
import type { KeyResult } from "@/api/hooks/goals"
import { toast } from "sonner"

const KR_COLOR = "#a78bfa"

interface Props {
  kr: KeyResult
  onEdit: (kr: KeyResult) => void
}

export function KeyResultItem({ kr, onEdit }: Props) {
  const del = useDeleteKeyResult(kr.goal_id)
  const pct = Math.min(Math.max(kr.progress_percent, 0), 100)

  return (
    <div className="flex flex-col gap-2 rounded-[6px] border border-border bg-surface-2 p-3">
      {/* Title + actions */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <p className="text-xs font-medium text-foreground">{kr.title}</p>
          {kr.description && (
            <p className="mt-0.5 text-[11px] text-muted-foreground">{kr.description}</p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <button
            onClick={() => onEdit(kr)}
            className="flex h-6 w-6 items-center justify-center rounded-[4px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
            aria-label="Edit key result"
          >
            <Pencil className="h-3 w-3" />
          </button>
          <button
            disabled={del.isPending}
            onClick={() => del.mutate(kr.id, {
              onSuccess: () => toast.success("Key result deleted"),
              onError:   () => toast.error("Failed to delete key result"),
            })}
            className="flex h-6 w-6 items-center justify-center rounded-[4px] text-destructive/60 transition-colors hover:bg-surface-3 hover:text-destructive disabled:opacity-50"
            aria-label="Delete key result"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-3">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${pct}%`,
                background: `linear-gradient(90deg, ${KR_COLOR} 0%, ${KR_COLOR}cc 100%)`,
                boxShadow: `0 0 8px ${KR_COLOR}60`,
              }}
              role="progressbar"
              aria-valuenow={pct}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </div>
        <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
          {kr.current_value} / {kr.target_value}{kr.unit ? ` ${kr.unit}` : ""}{" "}
          <span className="font-bold" style={{ color: KR_COLOR }}>
            {pct.toFixed(0)}%
          </span>
        </span>
      </div>
    </div>
  )
}
