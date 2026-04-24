import { useNavigate } from "react-router-dom"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useDeleteGoal } from "@/api/hooks/goals"
import type { Goal } from "@/api/hooks/goals"
import { toast } from "sonner"

interface Props {
  goal: Goal
  progressPercent: number
  keyResultsCount: number
}

export function GoalCard({ goal, progressPercent, keyResultsCount }: Props) {
  const navigate = useNavigate()
  const del = useDeleteGoal()

  const clamped = Math.min(Math.max(progressPercent, 0), 100)

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={() => navigate(`/goals/${goal.id}`)}
    >
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{goal.title}</CardTitle>
        <p className="text-xs text-muted-foreground capitalize">{goal.priority} priority</p>
      </CardHeader>
      <CardContent className="pb-3">
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
          <span>{keyResultsCount} key result{keyResultsCount !== 1 ? "s" : ""}</span>
          <span>{clamped.toFixed(0)}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${clamped}%` }}
            role="progressbar"
            aria-valuenow={clamped}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </CardContent>
      <CardFooter onClick={(e) => e.stopPropagation()}>
        <Button
          size="sm"
          variant="ghost"
          className="text-destructive hover:text-destructive"
          disabled={del.isPending}
          onClick={() =>
            del.mutate(goal.id, {
              onSuccess: () => toast.success("Goal deleted"),
              onError: () => toast.error("Failed to delete goal"),
            })
          }
        >
          Delete
        </Button>
      </CardFooter>
    </Card>
  )
}
