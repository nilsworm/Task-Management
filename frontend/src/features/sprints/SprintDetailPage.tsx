import { useParams } from "react-router-dom"

export function SprintDetailPage() {
  const { id } = useParams<{ id: string }>()
  return (
    <div>
      <h1 className="text-2xl font-bold">Sprint {id}</h1>
      <p className="mt-2 text-muted-foreground">Kanban board — coming in Step 4.</p>
    </div>
  )
}
