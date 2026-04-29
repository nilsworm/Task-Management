import { useState } from "react"
import { Plus } from "lucide-react"
import { useSprints } from "@/api/hooks/sprints"
import { SprintCard } from "./SprintCard"
import { SprintCreateModal } from "./SprintCreateModal"

function CardSkeleton() {
  return <div className="h-36 animate-pulse rounded-[6px] bg-surface-3" />
}

export function SprintsPage() {
  const [createOpen, setCreateOpen] = useState(false)
  const { data: sprints = [], isLoading, isError } = useSprints()

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-semibold text-foreground">Sprints</h1>
          <span className="font-mono text-[11px] text-muted-foreground">
            {isLoading ? "…" : sprints.length}
          </span>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="flex h-7 items-center gap-1.5 rounded-[5px] border border-border bg-surface-2 px-3 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-surface-3 hover:text-foreground"
        >
          <Plus className="h-3 w-3" />
          New sprint
        </button>
      </div>

      {isError && (
        <p className="text-[11px] text-destructive">
          Failed to load sprints. Is the backend running?
        </p>
      )}

      {isLoading && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => <CardSkeleton key={i} />)}
        </div>
      )}

      {!isLoading && !isError && sprints.length === 0 && (
        <p className="py-12 text-center text-[11px] text-muted-foreground">
          No sprints yet.
        </p>
      )}

      {!isLoading && !isError && sprints.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {sprints.map((sprint) => (
            <SprintCard key={sprint.id} sprint={sprint} />
          ))}
        </div>
      )}

      <SprintCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  )
}
