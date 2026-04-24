import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts"
import type { VelocityData } from "@/api/hooks/dashboard"

interface Props {
  velocity: VelocityData
}

export function VelocityWidget({ velocity }: Props) {
  const { sprints, average_velocity } = velocity

  const data = sprints.map((s) => ({
    name: s.sprint_name.length > 12 ? s.sprint_name.slice(0, 12) + "…" : s.sprint_name,
    points: s.completed_points,
  }))

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Velocity</h2>
        <span className="text-xs text-muted-foreground">
          Avg: {average_velocity.toFixed(1)} pts/sprint
        </span>
      </div>

      {data.length === 0 ? (
        <p className="py-4 text-center text-xs text-muted-foreground">
          No completed sprints yet.
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip
              formatter={(v) => [`${String(v ?? 0)} pts`, "Completed"]}
              contentStyle={{ fontSize: 12 }}
            />
            <Bar dataKey="points" radius={[4, 4, 0, 0]}>
              {data.map((_, i) => (
                <Cell key={i} fill="#60a5fa" />
              ))}
            </Bar>
            {average_velocity > 0 && (
              <ReferenceLine
                y={average_velocity}
                stroke="#f59e0b"
                strokeDasharray="4 2"
                label={{ value: "Avg", fontSize: 10, fill: "#f59e0b", position: "insideTopRight" }}
              />
            )}
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
