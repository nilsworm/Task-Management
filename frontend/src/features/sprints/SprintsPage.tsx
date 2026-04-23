import { useState } from "react"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useSprints } from "@/api/hooks/sprints"
import { SprintCard } from "./SprintCard"
import { SprintCreateModal } from "./SprintCreateModal"

export function SprintsPage() {
  const [createOpen, setCreateOpen] = useState(false)
  const { data: sprints = [], isLoading, isError } = useSprints()

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Sprints</h1>
          <p className="text-sm text-muted-foreground">
            {isLoading ? "Loading…" : `${sprints.length} sprint${sprints.length !== 1 ? "s" : ""}`}
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Sprint
        </Button>
      </div>

      {isError && (
        <p className="text-sm text-destructive">Failed to load sprints. Is the backend running?</p>
      )}

      {!isLoading && !isError && sprints.length === 0 && (
        <p className="py-12 text-center text-sm text-muted-foreground">
          No sprints yet. Create one to get started.
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sprints.map((sprint) => (
          <SprintCard key={sprint.id} sprint={sprint} />
        ))}
      </div>

      <SprintCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  )
}
