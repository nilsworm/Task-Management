import { useParams } from "react-router-dom"

export function GoalDetailPage() {
  const { id } = useParams<{ id: string }>()
  return (
    <div>
      <h1 className="text-2xl font-bold">Goal {id}</h1>
      <p className="mt-2 text-muted-foreground">Key results — coming in Step 5.</p>
    </div>
  )
}
