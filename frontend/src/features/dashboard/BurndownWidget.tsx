import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts"
import type { BurndownData } from "@/api/hooks/dashboard"

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

interface Props { burndown: BurndownData }

export function BurndownWidget({ burndown }: Props) {
  const { sprint_name, ideal_line, actual_remaining, total_points } = burndown
  const data = ideal_line.map((p) => ({ date: p.date, ideal: p.remaining_points }))

  const todayStr = new Date().toISOString().split("T")[0]
  const todayInRange = todayStr >= burndown.start_date && todayStr <= burndown.end_date

  return (
    <div className="flex flex-col gap-3.5 rounded-[6px] border border-border bg-surface-2 p-3.5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-[0.6px] text-muted-foreground">
          Burndown
        </span>
        <span className="max-w-[140px] truncate font-mono text-[11px] text-muted-foreground">
          {sprint_name}
        </span>
      </div>

      {/* Stats row */}
      <div className="flex gap-4">
        <div className="flex items-center gap-1.5">
          <span className="font-mono text-[11px] text-muted-foreground">Total</span>
          <span className="font-mono text-[11px] font-bold text-foreground">{total_points} pts</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="font-mono text-[11px] text-muted-foreground">Remaining</span>
          <span className="font-mono text-[11px] font-bold" style={{ color: "var(--color-green)" }}>
            {actual_remaining} pts
          </span>
        </div>
      </div>

      {data.length === 0 ? (
        <p className="py-8 text-center text-[11px] text-muted-foreground">No sprint data.</p>
      ) : (
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={data} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
            <CartesianGrid
              stroke="var(--color-border)"
              strokeOpacity={0.5}
              strokeDasharray="4 2"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tick={TICK_STYLE}
              axisLine={false}
              tickLine={false}
              tickFormatter={(d: string) => d.slice(5)}
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
              labelFormatter={(l) => `Date: ${String(l)}`}
              formatter={(v) => [`${String(v ?? 0)} pts`, "Ideal"]}
              cursor={{ stroke: "var(--color-border)", strokeWidth: 1 }}
            />
            <Line
              type="monotone"
              dataKey="ideal"
              stroke="var(--color-muted-foreground)"
              strokeDasharray="4 2"
              strokeWidth={1.5}
              dot={false}
              name="Ideal"
            />
            {todayInRange && (
              <ReferenceLine
                x={todayStr}
                stroke="var(--color-cyan)"
                strokeWidth={1.5}
                label={{ value: "Today", fontSize: 9, fill: "var(--color-cyan)", fontFamily: "var(--font-mono)" }}
              />
            )}
            <ReferenceLine
              y={actual_remaining}
              stroke="var(--color-green)"
              strokeDasharray="3 3"
              strokeWidth={1.5}
              label={{
                value: "Actual",
                fontSize: 9,
                fill: "var(--color-green)",
                position: "insideTopRight",
                fontFamily: "var(--font-mono)",
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
