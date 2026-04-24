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
const TOOLTIP_STYLE = {
  background: "var(--color-surface-1)",
  border: "1px solid var(--color-border)",
  borderRadius: 5,
  fontSize: 11,
  color: "var(--color-foreground)",
  boxShadow: "var(--shadow-med)",
}

const TICK_STYLE = {
  fontSize: 9,
  fill: "var(--color-muted-foreground)",
  fontFamily: "var(--font-mono)",
}

// Use a stable color — gradient via CSS filter trick
const BAR_COLOR = "#00d4ff"

interface Props { velocity: VelocityData }

export function VelocityWidget({ velocity }: Props) {
  const { sprints, average_velocity } = velocity

  const data = sprints.map((s) => ({
    name: s.sprint_name.length > 10 ? s.sprint_name.slice(0, 10) + "…" : s.sprint_name,
    points: s.completed_points,
  }))

  return (
    <div className="flex flex-col gap-3.5 rounded-[6px] border border-border bg-surface-2 p-3.5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-[0.6px] text-muted-foreground">
          Velocity
        </span>
        <span className="font-mono text-[11px] text-muted-foreground">
          Avg:{" "}
          <span className="font-bold" style={{ color: "var(--color-yellow)" }}>
            {average_velocity.toFixed(1)}
          </span>{" "}
          pts/sprint
        </span>
      </div>

      {data.length === 0 ? (
        <p className="py-8 text-center text-[11px] text-muted-foreground">
          No completed sprints yet.
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={data} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
            <CartesianGrid
              stroke="var(--color-border)"
              strokeOpacity={0.5}
              strokeDasharray="4 2"
              vertical={false}
            />
            <XAxis
              dataKey="name"
              tick={TICK_STYLE}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={TICK_STYLE}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              itemStyle={{ color: "var(--color-foreground)" }}
              labelStyle={{ color: "var(--color-muted-foreground)", fontSize: 10, marginBottom: 4 }}
              formatter={(v) => [`${String(v ?? 0)} pts`, "Completed"]}
              cursor={{ fill: "rgba(255,255,255,0.03)" }}
            />
            <Bar dataKey="points" radius={[3, 3, 0, 0]} maxBarSize={48}>
              {data.map((_, i) => (
                <Cell
                  key={i}
                  fill={BAR_COLOR}
                  style={{ filter: `drop-shadow(0 0 6px ${BAR_COLOR}60)` }}
                />
              ))}
            </Bar>
            {average_velocity > 0 && (
              <ReferenceLine
                y={average_velocity}
                stroke="var(--color-yellow)"
                strokeDasharray="4 2"
                strokeWidth={1.5}
                label={{
                  value: "Avg",
                  fontSize: 9,
                  fill: "var(--color-yellow)",
                  position: "insideTopRight",
                  fontFamily: "var(--font-mono)",
                }}
              />
            )}
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
