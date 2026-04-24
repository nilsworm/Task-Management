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

interface Props {
  burndown: BurndownData
}

export function BurndownWidget({ burndown }: Props) {
  const { sprint_name, ideal_line, actual_remaining, total_points } = burndown

  const data = ideal_line.map((p) => ({ date: p.date, ideal: p.remaining_points }))

  const todayStr = new Date().toISOString().split("T")[0]
  const todayInRange =
    todayStr >= burndown.start_date && todayStr <= burndown.end_date

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Burndown</h2>
        <span className="text-xs text-muted-foreground truncate max-w-[140px]">
          {sprint_name}
        </span>
      </div>

      <div className="flex gap-4 text-xs text-muted-foreground">
        <span>
          Total: <span className="font-medium text-foreground">{total_points} pts</span>
        </span>
        <span>
          Remaining:{" "}
          <span className="font-medium text-foreground">{actual_remaining} pts</span>
        </span>
      </div>

      {data.length === 0 ? (
        <p className="py-4 text-center text-xs text-muted-foreground">No sprint data.</p>
      ) : (
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10 }}
              tickFormatter={(d: string) => d.slice(5)}
            />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip
              labelFormatter={(l) => `Date: ${String(l)}`}
              formatter={(v) => [`${String(v ?? 0)} pts`, "Ideal"]}
              contentStyle={{ fontSize: 12 }}
            />
            <Line
              type="monotone"
              dataKey="ideal"
              stroke="#94a3b8"
              strokeDasharray="4 2"
              dot={false}
              name="Ideal"
            />
            {todayInRange && (
              <ReferenceLine
                x={todayStr}
                stroke="#60a5fa"
                strokeWidth={1.5}
                label={{ value: "Today", fontSize: 10, fill: "#60a5fa" }}
              />
            )}
            <ReferenceLine
              y={actual_remaining}
              stroke="#34d399"
              strokeDasharray="3 3"
              label={{ value: "Actual", fontSize: 10, fill: "#34d399", position: "insideTopRight" }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
